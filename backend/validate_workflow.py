import asyncio
import httpx

API_URL = "http://127.0.0.1:8000/api"

async def main():
    async with httpx.AsyncClient(base_url=API_URL) as client:
        # 1. Login Official
        print("1. Logging in Official...")
        resp = await client.post("/auth/login", json={"email": "official@aiip.gov.in", "password": "Demo@1234"})
        assert resp.status_code == 200, resp.text
        off_token = resp.json()["access_token"]
        off_headers = {"Authorization": f"Bearer {off_token}"}
        print("   -> Official Login Success")

        # 2. Get Hero Project
        print("\n2. Getting Hero Project...")
        resp = await client.get("/projects/hero", headers=off_headers)
        assert resp.status_code == 200, resp.text
        hero_id = resp.json()["id"]
        print(f"   -> Hero Project ID: {hero_id}")

        # 3. Assign Surprise Inspection
        print("\n3. Assigning Surprise Inspection...")
        resp = await client.post("/inspections/assign", headers=off_headers, json={"project_id": hero_id, "max_distance_km": 50.0})
        if resp.status_code != 200:
            print(f"FAILED ASSIGNMENT: {resp.status_code} {resp.text}")
            return
            
        assignment = resp.json()
        assign_id = assignment["assignment_id"]
        insp_id = assignment["inspector_id"]
        print(f"   -> Assignment ID: {assign_id} to Inspector ID: {insp_id}")

        # 4. Get the Inspector User (to login as inspector)
        print("\n4. Getting Inspector User Details...")
        # Actually we know it is likely insp1@aiip.gov.in or similar. We can just loop 1 to 5
        insp_email = None
        insp_token = None
        for i in range(1, 6):
            try:
                resp = await client.post("/auth/login", json={"email": f"insp{i}@aiip.gov.in", "password": "Demo@1234"})
                if resp.status_code == 200:
                    insp_token = resp.json()["access_token"]
                    # check if this is the assigned inspector
                    h = {"Authorization": f"Bearer {insp_token}"}
                    me = await client.get("/auth/me", headers=h)
                    
                    # Instead of parsing all, just fetch inspections and see if it's there
                    insps = await client.get("/inspections", headers=h)
                    for item in insps.json().get("items", []):
                        if item["project_id"] == hero_id:
                            insp_email = f"insp{i}@aiip.gov.in"
                            insp_actual_id = item["id"]
                            break
                    if insp_email:
                        break
            except Exception:
                continue
                
        if not insp_email:
            print("COULD NOT FIND ASSIGNED INSPECTOR!")
            return
            
        print(f"   -> Logged in as assigned Inspector: {insp_email} (Inspection ID: {insp_actual_id})")
        insp_headers = {"Authorization": f"Bearer {insp_token}"}

        # 5. Start Inspection
        print("\n5. Starting Inspection...")
        resp = await client.post(f"/inspections/{insp_actual_id}/start", headers=insp_headers, json={
            "latitude": 28.6139,
            "longitude": 77.2090,
            "gps_accuracy": 5.0,
            "offline": False
        })
        assert resp.status_code == 200, resp.text
        print("   -> Inspection Started")

        # 6. Submit Inspection
        print("\n6. Submitting Inspection...")
        submit_data = {
            "overall_rating": 80,
            "summary_notes": "All good.",
            "recommendations": "None.",
            "checklist_items": [
                {
                    "item_key": "operational_status",
                    "value": True,
                    "observation": "Operating normally",
                    "captured_offline": False
                }
            ]
        }
        resp = await client.post(f"/inspections/{insp_actual_id}/submit", headers=insp_headers, json=submit_data)
        assert resp.status_code == 200, resp.text
        print("   -> Inspection Submitted")

        # 7. Official Decision
        print("\n7. Making Official Decision...")
        resp = await client.post(f"/inspections/{insp_actual_id}/decision", headers=off_headers, json={
            "decision": "APPROVED",
            "decision_notes": "Reviewed and approved."
        })
        assert resp.status_code == 200, resp.text
        print("   -> Decision Made: APPROVED")

        print("\n=== E2E WORKFLOW VALIDATED ===")

if __name__ == "__main__":
    asyncio.run(main())
