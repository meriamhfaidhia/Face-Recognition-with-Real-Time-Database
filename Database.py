from supabase import create_client
import datetime

# Initialize
url = "https://cgfxkephzkmrijduhtua.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNnZnhrZXBoemttcmlqZHVodHVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ4NDIwMjAsImV4cCI6MjA2MDQxODAyMH0.VhuRuWRCQzlvBc1zr86k3B0quSq2xT5uBDNS8X3hNOI"
supabase = create_client(url, key)

data = {
    "852741": {
        "name": "Emily",
        "major": "Robotics",
        "starting_year": 2017,
        "total_attendance": 7,
        "standing": "G",
        "year": 4,
        "last_attendance_time": "2022-12-11 00:54:34"
    },
    "963852":
        {
            "name": "Elon Musk",
            "major": "Physics",
            "starting_year": 2020,
            "total_attendance": 7,
            "standing": "G",
            "year": 2,
            "last_attendance_time": "2022-12-11 00:54:34"
        }
}

try:
    # D'abord récupérer tous les IDs existants
    existing_users = supabase.table("Users").select("id").execute()
    existing_ids = [user['id'] for user in existing_users.data] if existing_users.data else []

    # Filtrer pour ne garder que les nouveaux utilisateurs
    new_users = {uid: data for uid, data in data.items() if uid not in existing_ids}

    if new_users:
        for user_id, user_data in new_users.items():
            response = supabase.table("Users").insert({
                "id": user_id,
                **user_data
            }).execute()
            print(f"Ajouté nouvel utilisateur {user_data['name']}: {response.data}")
    else:
        print("Aucun nouvel utilisateur à ajouter")

except Exception as e:
    print(f"Error: {e}")