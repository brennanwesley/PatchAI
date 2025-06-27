# PatchAI Enterprise SaaS Platform

## Project Vision
- AI-powered chat platform for both individual consumers and enterprise customers, branded as "PatchAI: your personal oilfield consultant." 
- PatchAI will provide custom feature sets specific to oil and gas work flows to provide users and enterprises more value that are not currently available with other AI chatbot platforms. I will continue to add new features and capabilities to the platform to provide users and enterprises with the best possible experience. I will make a sub category to detail each custome feature set in th is file.
- Custom feature sets:
- Subscription-based SaaS with Stripe integration
- Mobile-ready architecture

## Architecture Overview
- Backend: FastAPI + Python 3.11
- Frontend: React 19.1 + TailwindCSS  
- Database: Supabase PostgreSQL with RLS
- Auth: JWT tokens via Supabase Auth
- Payments: Stripe webhooks and subscriptions

## Development Standards
- Python: PEP8, type hints, Google docstrings
- NEW RULE FOR FILES GOING FORWARD: File limit 500 lines max, appropriately refactor code to achieve this rule.
- Testing: Pytest with 3 test cases minimum
- Module structure: core/, services/, routes/

## Current State
- Version 2.0.0 proprietary
- Enterprise architecture implemented
- Ready for mobile expansion