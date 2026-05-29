import ipaddress
import json
import logging
import socket
import urllib.parse

import requests
from bs4 import BeautifulSoup
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import RecipeForm, RegisterForm
from .models import Recipe, Tag

logger = logging.getLogger(__name__)

_SCRAPE_MAX_BYTES = 2 * 1024 * 1024  # 2MB cap on scraped pages


def home(request):
    return redirect('recipe_list' if request.user.is_authenticated else 'login')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('recipe_list')
    error = ''
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
            if user:
                login(request, user)
                return redirect('recipe_list')
        except User.DoesNotExist:
            pass
        error = 'Invalid email or password.'
    return render(request, 'auth/login.html', {'error': error})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('recipe_list')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('recipe_list')
    return render(request, 'auth/register.html', {'form': form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def recipe_list(request):
    query = request.GET.get('q', '').strip()
    tag_id = request.GET.get('tag', '').strip()
    if tag_id and not tag_id.isdigit():
        tag_id = ''

    recipes = Recipe.objects.filter(user=request.user).prefetch_related('tags')
    if query:
        recipes = recipes.filter(title__icontains=query)
    if tag_id:
        recipes = recipes.filter(tags__id=tag_id).distinct()

    active_tag = None
    if tag_id:
        active_tag = Tag.objects.filter(id=tag_id, user=request.user).first()

    return render(request, 'recipes/list.html', {
        'recipes': recipes,
        'query': query,
        'active_tag': active_tag,
        'active_tag_id': tag_id,
    })


@login_required
def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe.objects.prefetch_related('tags'), pk=pk, user=request.user)
    return render(request, 'recipes/detail.html', {'recipe': recipe})


def _form_context(request, form, recipe=None):
    if recipe:
        ingredients = recipe.ingredients or ['']
        steps = recipe.steps or ['']
        selected_ids = [str(t.id) for t in recipe.tags.all()]
        initial_rating = recipe.rating or 0
    else:
        ingredients = ['']
        steps = ['']
        selected_ids = []
        initial_rating = 0

    if request.method == 'POST':
        ingredients_raw = request.POST.get('ingredients_json', '[]')
        steps_raw = request.POST.get('steps_json', '[]')
        try:
            ingredients = json.loads(ingredients_raw)
        except (json.JSONDecodeError, ValueError):
            ingredients = ['']
        try:
            steps = json.loads(steps_raw)
        except (json.JSONDecodeError, ValueError):
            steps = ['']
        selected_ids = request.POST.getlist('tag_ids')
        initial_rating = request.POST.get('rating', '') or 0

    return {
        'form': form,
        'recipe': recipe,
        'tags': Tag.objects.filter(user=request.user).order_by('name'),
        'ingredients_json': ingredients if ingredients else [''],
        'steps_json': steps if steps else [''],
        'selected_tag_ids_json': selected_ids,
        'initial_rating': int(initial_rating),
    }


def _apply_recipe_post(request, recipe):
    """Save POST-sourced fields (ingredients, steps, rating, tags) onto a recipe after form.save(commit=False)."""
    recipe.ingredients = _parse_json_list(request.POST.get('ingredients_json', '[]'))
    recipe.steps = _parse_json_list(request.POST.get('steps_json', '[]'))
    rating_val = request.POST.get('rating', '')
    if rating_val and rating_val.isdigit():
        r = int(rating_val)
        recipe.rating = r if 1 <= r <= 5 else None
    else:
        recipe.rating = None
    recipe.save()
    recipe.tags.set(Tag.objects.filter(id__in=request.POST.getlist('tag_ids'), user=request.user))


@login_required
def recipe_create(request):
    if request.method == 'POST':
        form = RecipeForm(request.POST)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.user = request.user
            _apply_recipe_post(request, recipe)
            return redirect('recipe_detail', pk=recipe.pk)
        return render(request, 'recipes/form.html', _form_context(request, form))
    return render(request, 'recipes/form.html', _form_context(request, RecipeForm()))


@login_required
def recipe_edit(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, user=request.user)
    if request.method == 'POST':
        form = RecipeForm(request.POST, instance=recipe)
        if form.is_valid():
            recipe = form.save(commit=False)
            _apply_recipe_post(request, recipe)
            return redirect('recipe_detail', pk=recipe.pk)
        return render(request, 'recipes/form.html', _form_context(request, form, recipe))
    return render(request, 'recipes/form.html', _form_context(request, RecipeForm(instance=recipe), recipe))


@login_required
def recipe_delete(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, user=request.user)
    if request.method == 'POST':
        recipe.delete()
        return redirect('recipe_list')
    return render(request, 'recipes/confirm_delete.html', {'recipe': recipe})


@login_required
@require_POST
def scrape_url(request):
    try:
        data = json.loads(request.body)
        url = data.get('url', '').strip()
        if not url:
            return JsonResponse({'error': 'URL required'}, status=400)

        safe, err = _check_url_safe(url)
        if not safe:
            return JsonResponse({'error': err}, status=400)

        headers = {'User-Agent': 'Mozilla/5.0 (compatible; RecipeSaver/1.0)'}
        resp = requests.get(url, timeout=10, headers=headers, stream=True)
        resp.raise_for_status()

        chunks = []
        total = 0
        for chunk in resp.iter_content(chunk_size=8192):
            chunks.append(chunk)
            total += len(chunk)
            if total > _SCRAPE_MAX_BYTES:
                raise ValueError('Response too large')

        encoding = resp.encoding or 'utf-8'
        html = b''.join(chunks).decode(encoding, errors='replace')
        soup = BeautifulSoup(html, 'html.parser')

        def og(prop):
            tag = soup.find('meta', property=f'og:{prop}')
            return tag['content'] if tag and tag.get('content') else ''

        title = og('title') or (soup.title.string.strip() if soup.title else '')
        return JsonResponse({
            'title': title,
            'description': og('description'),
            'thumbnail': og('image'),
        })
    except requests.RequestException:
        return JsonResponse({'error': 'Failed to fetch URL'}, status=400)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception:
        logger.exception('Unexpected error in scrape_url')
        return JsonResponse({'error': 'An unexpected error occurred'}, status=400)


@login_required
@require_POST
def tag_create(request):
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        color = data.get('color', '#6366f1')
        if not name:
            return JsonResponse({'error': 'Name required'}, status=400)
        tag, _ = Tag.objects.get_or_create(name=name, user=request.user, defaults={'color': color})
        return JsonResponse({'id': tag.id, 'name': tag.name, 'color': tag.color})
    except Exception:
        logger.exception('Unexpected error in tag_create')
        return JsonResponse({'error': 'An unexpected error occurred'}, status=400)


def _check_url_safe(url):
    """
    Validate that a URL targets a public address, not an internal/private one.
    Uses getaddrinfo to check all resolved IPs (both IPv4 and IPv6).
    Note: full DNS-rebinding protection would require validating at socket-connect time.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False, 'Only http/https URLs are allowed'
        hostname = parsed.hostname
        if not hostname:
            return False, 'Invalid URL'
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        try:
            infos = socket.getaddrinfo(hostname, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        except socket.gaierror:
            return False, 'Could not resolve hostname'
        if not infos:
            return False, 'Could not resolve hostname'
        for info in infos:
            addr = ipaddress.ip_address(info[4][0])
            if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
                return False, 'Requests to internal addresses are not allowed'
        return True, None
    except Exception:
        return False, 'Invalid URL'


def _parse_json_list(raw):
    try:
        result = json.loads(raw)
        return [s for s in result if isinstance(s, str) and s.strip()]
    except (json.JSONDecodeError, ValueError):
        return []
