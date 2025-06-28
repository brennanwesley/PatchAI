#!/usr/bin/env python3
"""
COMPREHENSIVE SUBSCRIPTION AUDIT
Find and fix ALL users with legacy subscription sync issues
"""

import os
import sys
import asyncio
import stripe
from dotenv import load_dotenv
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.supabase_service import supabase

# Load environment variables
load_dotenv()

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

async def comprehensive_audit():
    """Comprehensive audit of all users for subscription sync issues"""
    print("[COMPREHENSIVE AUDIT] All Users Subscription Sync")
    print("=" * 60)
    
    issues_found = []
    fixes_applied = []
    
    try:
        # Step 1: Get all users from database
        print("[Step 1] Getting all users from database...")
        users_response = supabase.table("user_profiles").select(
            "id, email, subscription_status, plan_tier, stripe_customer_id, last_payment_at"
        ).execute()
        
        if not users_response.data:
            print("[ERROR] No users found in database")
            return
        
        users = users_response.data
        print(f"[SUCCESS] Found {len(users)} users in database")
        
        # Step 2: Check each user against Stripe
        print(f"\n[Step 2] Auditing each user against Stripe...")
        print("-" * 60)
        
        for i, user in enumerate(users):
            user_id = user['id']
            email = user['email']
            db_status = user['subscription_status']
            db_plan = user['plan_tier']
            stripe_customer_id = user['stripe_customer_id']
            last_payment = user['last_payment_at']
            
            print(f"\n[{i+1}/{len(users)}] Checking {email}")
            print(f"   DB Status: {db_status}")
            print(f"   DB Plan: {db_plan}")
            print(f"   Stripe ID: {stripe_customer_id}")
            print(f"   Last Payment: {last_payment}")
            
            # Skip users without Stripe customer ID
            if not stripe_customer_id:
                print("   [SKIP] No Stripe customer ID")
                continue
            
            try:
                # Get Stripe customer data
                customer = stripe.Customer.retrieve(stripe_customer_id)
                subscriptions = stripe.Subscription.list(customer=stripe_customer_id, limit=10)
                invoices = stripe.Invoice.list(customer=stripe_customer_id, limit=20)
                
                # Analyze Stripe data
                active_subs = [s for s in subscriptions.data if s.status == 'active']
                paid_invoices = [inv for inv in invoices.data if inv.status == 'paid']
                total_paid = sum(inv.amount_paid / 100 for inv in paid_invoices)
                
                print(f"   Stripe Active Subs: {len(active_subs)}")
                print(f"   Stripe Paid Invoices: {len(paid_invoices)}")
                print(f"   Stripe Total Paid: ${total_paid}")
                
                # Detect sync issues
                issue_detected = False
                issue_description = []
                
                # Issue 1: Has active Stripe subscription but DB shows inactive
                if len(active_subs) > 0 and db_status != 'active':
                    issue_detected = True
                    issue_description.append(f"Stripe has {len(active_subs)} active subs but DB status is '{db_status}'")
                
                # Issue 2: Has paid invoices but DB shows no plan
                if total_paid > 0 and db_plan in ['none', None, '']:
                    issue_detected = True
                    issue_description.append(f"Stripe shows ${total_paid} paid but DB plan is '{db_plan}'")
                
                # Issue 3: Has paid invoices but no last_payment_at
                if total_paid > 0 and not last_payment:
                    issue_detected = True
                    issue_description.append(f"Stripe shows ${total_paid} paid but DB has no last_payment_at")
                
                # Issue 4: Multiple active subscriptions (billing issue)
                if len(active_subs) > 1:
                    issue_detected = True
                    issue_description.append(f"Multiple active subscriptions: {len(active_subs)} (potential double billing)")
                
                if issue_detected:
                    print(f"   [ISSUE DETECTED] {'; '.join(issue_description)}")
                    
                    issue_record = {
                        'user_id': user_id,
                        'email': email,
                        'db_status': db_status,
                        'db_plan': db_plan,
                        'stripe_customer_id': stripe_customer_id,
                        'stripe_active_subs': len(active_subs),
                        'stripe_paid_invoices': len(paid_invoices),
                        'stripe_total_paid': total_paid,
                        'issues': issue_description,
                        'needs_fix': True
                    }
                    issues_found.append(issue_record)
                    
                    # Auto-fix if it's a clear case
                    if len(active_subs) > 0 and db_status != 'active' and total_paid > 0:
                        print(f"   [AUTO-FIX] Applying fix...")
                        
                        fix_success = await apply_fix(user_id, email, stripe_customer_id, active_subs[0], total_paid)
                        
                        if fix_success:
                            print(f"   [FIX SUCCESS] User fixed")
                            fixes_applied.append(email)
                            issue_record['fixed'] = True
                        else:
                            print(f"   [FIX FAILED] Manual intervention required")
                            issue_record['fixed'] = False
                    else:
                        print(f"   [MANUAL] Requires manual review")
                        issue_record['fixed'] = False
                else:
                    print(f"   [OK] No issues detected")
                
            except stripe.error.InvalidRequestError as e:
                if "No such customer" in str(e):
                    print(f"   [ISSUE] Invalid Stripe customer ID: {stripe_customer_id}")
                    issues_found.append({
                        'user_id': user_id,
                        'email': email,
                        'db_status': db_status,
                        'db_plan': db_plan,
                        'stripe_customer_id': stripe_customer_id,
                        'issues': ['Invalid Stripe customer ID'],
                        'needs_fix': True,
                        'fixed': False
                    })
                else:
                    print(f"   [ERROR] Stripe API error: {str(e)}")
            
            except Exception as e:
                print(f"   [ERROR] Unexpected error: {str(e)}")
        
        # Step 3: Summary Report
        print(f"\n" + "=" * 60)
        print(f"[AUDIT COMPLETE] Summary Report")
        print(f"=" * 60)
        print(f"Total Users Audited: {len(users)}")
        print(f"Issues Found: {len(issues_found)}")
        print(f"Auto-Fixes Applied: {len(fixes_applied)}")
        print(f"Manual Review Required: {len([i for i in issues_found if not i.get('fixed', False)])}")
        
        if issues_found:
            print(f"\n[DETAILED ISSUES]")
            print("-" * 40)
            
            for issue in issues_found:
                print(f"\nUser: {issue['email']}")
                print(f"  Status: {issue['db_status']} -> {'FIXED' if issue.get('fixed') else 'NEEDS MANUAL FIX'}")
                print(f"  Issues: {'; '.join(issue['issues'])}")
                if issue.get('stripe_total_paid', 0) > 0:
                    print(f"  Stripe Paid: ${issue['stripe_total_paid']}")
        
        if fixes_applied:
            print(f"\n[AUTO-FIXED USERS]")
            print("-" * 20)
            for email in fixes_applied:
                print(f"  ✅ {email}")
        
        manual_fixes = [i for i in issues_found if not i.get('fixed', False)]
        if manual_fixes:
            print(f"\n[MANUAL REVIEW REQUIRED]")
            print("-" * 30)
            for issue in manual_fixes:
                print(f"  ⚠️  {issue['email']}: {'; '.join(issue['issues'])}")
        
        print(f"\n[FINAL RESULT]")
        if len(issues_found) == 0:
            print("🎉 ALL USERS ARE PROPERLY SYNCED!")
        elif len(fixes_applied) == len(issues_found):
            print("🎉 ALL ISSUES HAVE BEEN AUTO-FIXED!")
        else:
            print(f"⚠️  {len(manual_fixes)} USERS REQUIRE MANUAL INTERVENTION")
        
        return {
            'total_users': len(users),
            'issues_found': len(issues_found),
            'fixes_applied': len(fixes_applied),
            'manual_required': len(manual_fixes),
            'issues': issues_found
        }
        
    except Exception as e:
        print(f"[ERROR] Audit failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def apply_fix(user_id, email, stripe_customer_id, active_subscription, total_paid):
    """Apply automatic fix for clear sync issues"""
    try:
        # Update user profile
        update_data = {
            "subscription_status": "active",
            "plan_tier": "standard",
            "last_payment_at": datetime.now().isoformat()
        }
        
        profile_update = supabase.table("user_profiles").update(update_data).eq("id", user_id).execute()
        
        return True
        
    except Exception as e:
        print(f"   [FIX ERROR] {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(comprehensive_audit())
    
    if result:
        print(f"\n" + "=" * 60)
        print(f"[AUDIT STATISTICS]")
        print(f"Total Users: {result['total_users']}")
        print(f"Issues Found: {result['issues_found']}")
        print(f"Auto-Fixed: {result['fixes_applied']}")
        print(f"Manual Required: {result['manual_required']}")
        print(f"Success Rate: {(result['fixes_applied'] / max(result['issues_found'], 1)) * 100:.1f}%")
    else:
        print("\n[FAILED] Audit could not be completed")
