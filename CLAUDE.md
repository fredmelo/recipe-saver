# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
npm run dev       # Start development server
npm run build     # Build production bundle
npm run lint      # Run ESLint via Next.js
npx prisma db push      # Sync schema changes to the SQLite database
npx prisma studio       # Open Prisma GUI for inspecting data
```

There is no test suite configured.

## Architecture

Full-stack Next.js 14 (App Router) recipe management app with SQLite + Prisma, NextAuth.js credentials auth, and Tailwind CSS.

### Route groups

- `src/app/(auth)/` — unauthenticated pages (login, register); protected by their own layout
- `src/app/(app)/` — authenticated pages (recipes list, detail, create, edit); `layout.tsx` here enforces session and renders `AppSidebar`
- `src/app/api/` — REST-style API routes: `/recipes`, `/recipes/[id]`, `/tags`, `/tags/[id]`, `/auth/[...nextauth]`, `/auth/register`, `/scrape`

### Data flow

API routes in `src/app/api/` call Prisma directly via the singleton in `src/lib/db.ts`. Pages fetch from these API routes client-side or via server components. `src/lib/auth.ts` configures NextAuth and is imported by the catch-all auth route and any server-side session checks.

### Database

SQLite file, schema in `prisma/schema.prisma`. Four models: `User`, `Recipe`, `Tag`, `RecipeTag` (many-to-many junction). Ingredients and steps are stored as JSON arrays on `Recipe`. After any schema change, run `npx prisma db push`.

### Key conventions

- Path alias `@/*` resolves to `src/*`
- `src/lib/utils.ts` exports `cn()` (clsx + tailwind-merge) — use it for conditional class names
- NextAuth session is extended in `src/types/next-auth.d.ts` to include `user.id`
- `next.config.js` allows remote images from any hostname — needed for scraped recipe thumbnails
