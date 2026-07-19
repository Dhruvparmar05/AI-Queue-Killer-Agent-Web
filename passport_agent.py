# passport_agent.py
import asyncio
import base64
from playwright.async_api import async_playwright

class PassportAgent:
    def __init__(self, ai_data, supabase_client, record_id):
        self.ai_data = ai_data
        self.db = supabase_client
        self.record_id = record_id
        self.page = None
        self.browser = None

    async def run_pipeline(self):
        async with async_playwright() as p:
            print(f"[Agent-{self.record_id}]: Launching Live Browser Core...")
            self.browser = await p.chromium.launch(
                headless=False, 
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 800}
            )
            self.page = await context.new_page()

            try:
                # 1. Open Passport Seva Main Portal
                await self.page.goto("https://www.passportindia.gov.in/AppOnlineProject/welcomeLink", timeout=60000)
                await asyncio.sleep(2)
                
                # Close potential banner modals
                try:
                    await self.page.click("button:has-text('Close')", timeout=3000)
                except:
                    pass

                # 2. Click User Login Layout
                await self.page.click("a:has-text('Existing User Login')")
                await self.page.wait_for_load_state("networkidle")

                # 3. Enter Username logic
                username = self.ai_data.get("username", "TEST_USER")
                await self.page.fill("#loginId", username)
                await self.page.click("#submitLoginId")
                await asyncio.sleep(2)

                # 4. Enter Password
                password = self.ai_data.get("password", "TEST_PASS")
                await self.page.fill("#pwd", password)

                # 5. Handle Live Captcha Processing
                await self.process_captcha_loop()

                # 6. Session Slot Check loop
                await self.execute_slot_hunter()

            except Exception as e:
                print(f"[Agent Error]: {str(e)}")
                self.db.table("queue_logs").update({"status": f"Failed: {str(e)}"}).eq("id", self.record_id).execute()
            finally:
                if self.browser:
                    await self.browser.close()

    async def process_captcha_loop(self):
        print("[Agent]: Locating Captcha Segment Image...")
        await self.page.wait_for_selector("#captchaImg")
        captcha_element = await self.page.query_selector("#captchaImg")
        
        if captcha_element:
            screenshot_bytes = await captcha_element.screenshot()
            base64_img = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Push updates out to let dynamic UI render captcha frame
            self.db.table("queue_logs").update({
                "status": "WAITING_FOR_CAPTCHA",
                "captcha_img": base64_img
            }).eq("id", self.record_id).execute()
            
            print("[Agent]: Awaiting valid user injection values via UI Console Dashboard...")
            
            # Watch out state inside database tracking structure
            while True:
                res = self.db.table("queue_logs").select("captcha_value").eq("id", self.record_id).single().execute()
                captcha_input = res.data.get("captcha_value") if res.data else None
                
                if captcha_input and captcha_input.strip() != "":
                    print(f"[Agent]: Injecting matching UI Token -> {captcha_input}")
                    await self.page.fill("#captcha", captcha_input)
                    await self.page.click("#submitPassword")
                    await asyncio.sleep(3)
                    break
                await asyncio.sleep(2)

    async def execute_slot_hunter(self):
        self.db.table("queue_logs").update({"status": "MONITORING_SLOTS"}).eq("id", self.record_id).execute()
        
        # Infinite slot extraction tracking cycle loop
        for check_cycle in range(5): 
            print(f"[Agent]: Checking slots context sequence: Cycle {check_cycle + 1}")
            # Target elements evaluation logic check matches...
            await asyncio.sleep(5)
            
        # Mock success verification point for debugging flow integration
        self.db.table("queue_logs").update({"status": "Success Booked"}).eq("id", self.record_id).execute()
        print("[Agent]: Queue Killed successfully!")