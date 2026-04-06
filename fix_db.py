from firebase_config import db

members = {m.to_dict().get("name"): m.to_dict().get("email") for m in db.collection("members").stream()}

records = db.collection("attendance").stream()
for r in records:
    data = r.to_dict()
    present = data.get("present", [])
    absent = data.get("absent", [])
    
    new_present = [members.get(p, p) if p in members else p for p in present]
    new_absent = [members.get(a, a) if a in members else a for a in absent]
    
    db.collection("attendance").document(r.id).update({
        "present": new_present,
        "absent": new_absent
    })
    print(f"Updated {r.id}: {present} -> {new_present}")
print("Done")
