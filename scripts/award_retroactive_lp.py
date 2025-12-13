"""
One-time script to award retroactive LP to users for their existing verified terminals and routes.
Run with: python manage.py shell < scripts/award_retroactive_lp.py
"""
import random
from django.contrib.auth.models import User
from api.models import Terminal, Route, UserProfile

print("Awarding retroactive Lakbay Points...")
print("-" * 60)

for user in User.objects.all():
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    # Skip users who already have LP
    if profile.lakbay_points > 0:
        continue
    
    # Count verified terminals and routes
    verified_terminals = user.added_terminals.filter(verified=True).count()
    verified_routes = user.added_routes.filter(verified=True).count()
    
    # Skip users with no contributions
    if verified_terminals == 0 and verified_routes == 0:
        continue
    
    # Award 20-80 random LP per verified terminal
    terminal_lp = sum(random.randint(20, 80) for _ in range(verified_terminals))
    
    # Award 20-80 random LP per verified route
    route_lp = sum(random.randint(20, 80) for _ in range(verified_routes))
    
    # Also add rating points (1 LP per rating point on their terminals)
    rating_lp = sum(t.rating for t in user.added_terminals.filter(verified=True))
    
    total_lp = terminal_lp + route_lp + rating_lp
    
    profile.lakbay_points = total_lp
    profile.save()
    
    print(f"{user.username}:")
    print(f"  - {verified_terminals} terminals = {terminal_lp} LP")
    print(f"  - {verified_routes} routes = {route_lp} LP")
    print(f"  - {rating_lp} rating LP")
    print(f"  - TOTAL: {total_lp} LP")
    print()

print("-" * 60)
print("Done!")
