from locust import HttpUser, task, between
import random

class SimpleTester(HttpUser):
    # ضع هنا المضيف الكامل
    host = "http://api:8000"  # هذا سيصبح المضيف الأساسي لجميع الطلبات
    wait_time = between(1, 2)

    @task
    def test_interaction(self):
        payload = {"user_id": int(random.randint(0, 99999999))}

        # الآن يمكنك استخدام المسار النسبي فقط
        with self.client.post(
            "/api/recommender",
            json=payload,
            catch_response=True,
            name="/api/recommender",
        ) as response:
            if response.status_code in (200, 201):
                response.success()
            else:
                print(f"Failed payload: {payload}")
                print(f"HTTP {response.status_code}: {response.text}")
                response.failure(f"HTTP {response.status_code}")
