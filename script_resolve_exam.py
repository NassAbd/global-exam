from playwright.sync_api import sync_playwright
import os
import random
import time
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

def human_delay(min_s=1, max_s=3):
    time.sleep(random.uniform(min_s, max_s))

# Mouse movement utilities
def bezier_point(t, p0, p1, p2, p3):
    """Calculate a point on a cubic Bezier curve."""
    u = 1 - t
    tt = t * t
    uu = u * u
    uuu = uu * u
    ttt = tt * t
    
    x = uuu * p0[0] + 3 * uu * t * p1[0] + 3 * u * tt * p2[0] + ttt * p3[0]
    y = uuu * p0[1] + 3 * uu * t * p1[1] + 3 * u * tt * p2[1] + ttt * p3[1]
    return (x, y)

# Track last mouse position for realistic movement
LAST_MOUSE_POS = None

def get_start_point(page, width, height):
    """Get realistic starting point (last known position or random edge)."""
    global LAST_MOUSE_POS
    if LAST_MOUSE_POS:
        return LAST_MOUSE_POS
    
    edge = random.choice(['top', 'bottom', 'left', 'right'])
    if edge == 'top':
        return (random.randint(0, width), 0)
    elif edge == 'bottom':
        return (random.randint(0, width), height)
    elif edge == 'left':
        return (0, random.randint(0, height))
    else:
        return (width, random.randint(0, height))

def human_mouse_move(page, end_x, end_y):
    """Move mouse to (end_x, end_y) with overshoot and correction for human-like behavior."""
    global LAST_MOUSE_POS
    
    vp = page.viewport_size
    width, height = (vp['width'], vp['height']) if vp else (1440, 900)
    
    start_x, start_y = get_start_point(page, width, height)
    
    overshoot = False
    dist = ((end_x - start_x)**2 + (end_y - start_y)**2)**0.5
    if dist > 300 and random.random() < 0.3:
        overshoot = True
        
    ctrl1_x = start_x + (end_x - start_x) * random.uniform(0.15, 0.45) + random.uniform(-50, 50)
    ctrl1_y = start_y + (end_y - start_y) * random.uniform(0.15, 0.45) + random.uniform(-50, 50)
    
    ctrl2_x = start_x + (end_x - start_x) * random.uniform(0.55, 0.85) + random.uniform(-50, 50)
    ctrl2_y = start_y + (end_y - start_y) * random.uniform(0.55, 0.85) + random.uniform(-50, 50)
    
    target_x, target_y = end_x, end_y
    if overshoot:
        overshoot_dist = random.uniform(10, 30)
        target_x += list(map(lambda x: x * overshoot_dist, [random.choice([-1, 1])]))[0]
        target_y += random.choice([-1, 1]) *  random.uniform(5, 10)

    steps_count = random.randint(30, 60)
    
    for i in range(steps_count + 1):
        t = i / steps_count
        noise = random.uniform(-1, 1) * (1 - t)
        p = bezier_point(t, (start_x, start_y), (ctrl1_x, ctrl1_y), (ctrl2_x, ctrl2_y), (target_x, target_y))
        page.mouse.move(p[0] + noise, p[1] + noise, steps=1)
        if i % 10 == 0 and random.random() < 0.2:
             time.sleep(random.uniform(0.001, 0.010))

    if overshoot:
        time.sleep(random.uniform(0.05, 0.15))
        page.mouse.move(end_x, end_y, steps=random.randint(5, 10))
    
    LAST_MOUSE_POS = (end_x, end_y)


def real_click(page, selector):
    """Simulate realistic click with curved mouse movement and random targeting."""
    try:
        element = page.locator(selector).first
        element.wait_for(state="visible", timeout=10000)
        box = element.bounding_box()
        if not box:
            return False

        target_x = box["x"] + box["width"] * random.uniform(0.3, 0.7)
        target_y = box["y"] + box["height"] * random.uniform(0.3, 0.7)

        human_mouse_move(page, target_x, target_y)
        
        human_delay(0.1, 0.3)
        page.mouse.down()
        time.sleep(random.uniform(0.05, 0.15))
        page.mouse.up()
        return True
    except Exception:
        return False

def handle_cookies(page):
    """Accept cookies if the banner appears."""
    try:
        btn = page.locator("button#axeptio_btn_acceptAll")
        if btn.is_visible():
            btn.click()
            print("✅ Cookies accepted")
            page.locator("#axeptio_overlay").wait_for(state="hidden", timeout=5000)
    except TimeoutError:
        pass
    except Exception:
        pass


def safe_click(page, selector, timeout=5000):
    """Click an element, retrying after handling cookies if needed."""
    try:
        page.locator(selector).wait_for(state="visible", timeout=timeout)
        page.click(selector)
        return True
    except Exception as e:
        print(f"⚠️ Failed to click {selector} ({e}), retrying after handling cookies")
        handle_cookies(page)
        try:
            page.locator(selector).wait_for(state="visible", timeout=timeout)
            page.click(selector)
            return True
        except Exception as e2:
            print(f"❌ Cannot click {selector} after retry ({e2})")
            return False




def safe_goto(page, url):
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
    except TimeoutError:
        print(f"⚠️ Timeout loading {url}, retrying...")
        handle_cookies(page)
        page.goto(url, wait_until="domcontentloaded", timeout=60000)


def safe_fill(page, selector, value, timeout=5000):
    """Fill an input field, retrying after handling cookies if needed."""
    try:
        page.locator(selector).wait_for(state="visible", timeout=timeout)
        page.fill(selector, value)
        return True
    except Exception as e:
        print(f"⚠️ Failed to fill {selector} ({e}), retrying after handling cookies")
        handle_cookies(page)
        try:
            page.locator(selector).wait_for(state="visible", timeout=timeout)
            page.fill(selector, value)
            return True
        except Exception as e2:
            print(f"❌ Cannot fill {selector} after retry ({e2})")
            return False


def choose_ipssi(page):
    selector = "div[onclick*='form-organization-selection-939']"
    handle_cookies(page)
    print("⏳ Reading page...")
    human_delay(3, 6)

    if page.locator(selector).count() > 0:
        print("✅ Selecting IPSSI organization...")
        if real_click(page, selector):
            try:
                page.wait_for_url("**/dashboard", timeout=15000, wait_until="domcontentloaded")
                print("✅ Navigated to dashboard")
            except Exception:
                print("⚠️  Dashboard navigation timeout (proceeding anyway)")
    else:
        print("ℹ️  No IPSSI selection needed")




def check_hours_exam(page):
    """Check exam hours counter."""
    try:
        safe_goto(page, "https://exam.global-exam.com/")
        handle_cookies(page)
        human_delay(1, 2)
        
        exam_button_selector = 'button:has-text("EXAM")'
        try:
            exam_button = page.locator(exam_button_selector).first
            exam_button.scroll_into_view_if_needed(timeout=5000)
            human_delay(0.5, 1)
            real_click(page, exam_button_selector)
            human_delay(1, 2)
        except Exception:
            pass
        
        hours_selector = 'span.text-24.font-bold.leading-6'
        
        if page.locator(hours_selector).count() > 1 and page.locator(hours_selector).nth(1).is_visible():
            raw_time = page.locator(hours_selector).nth(1).inner_text().strip()
            parts = raw_time.split('h')
            if len(parts) >= 1:
                hours_str = parts[0].strip()
                hours = int(hours_str)
                print(f"⏱️  Current EXAM hours: {hours}")
                return hours
        
        print("ℹ️  Could not detect exam hours")
        return 0
        
    except Exception as e:
        print(f"❌ Error checking hours: {e}")
        return 0



EXAM_QA_MAP = {
    "The staff would like to remind": "of",
    "The original timetable set": "has been changed",
    "Due to the abrupt departure": "will be",
    "The CEO of the company wishes": "close",
    "The conference on modern management": "has been rescheduled",
    "the company declines all responsibility": "originally",
    "Next week's company meeting": "will take place",
    "meeting you at the hotel": "of",
    "we have to postpone the annual": "unforeseen",
    "The accounting department would like": "have to be",
    "regarding the interview that we had planned": "am contacting",
    "The recent months": "therefore",
    "Global Cars is about to": "embark",
    "The sales manager has decided to": "call off",
    "the mechanic change the tires": "had",
    "Mr. Jameson considers his greatest": "achievement",
    "There are two different offers": "neither",
    "Last week's interview with Mr. Paulson": "should",
    "the movie by Lindberg": "Have you seen",
    "Last week's conference": "was",
    "Mr. Jackson requests": "as",
    "The accountant has asked the sales": "regarding",
    "Mr. Gerald asked his assistant": "to print",
    "The company is happy to announce": "will take",
    "due to a lack of funding": "cancelled",
    "The current sales team": "would like",
    "Each document that is edited by our company": "should",
    "to apply for a new job": "wanted",
    "Everyone is looking for a good": "position",
    "that the Internet is good and bad": "say",
}


def solve_exam_question(page, question_container):
    try:
        question_element = question_container.locator('p.text-neutral-80.leading-tight.mb-8').first
        
        try:
            if not question_element.is_visible(timeout=2000):
                raise Exception("Primary question element not visible")
        except:
            print("      🔄 Using fallback selector for question element")
            question_element = question_container.locator('span.block.w-full.overflow-y-auto.font-semibold.text-primary-900 p').first
            if not question_element.is_visible(timeout=2000):
                print("      ❌ Fallback question element also not visible")
                return False
        
        question_text = question_element.inner_text().strip().replace('\n', ' ')
        print(f"      📖 Question text: '{question_text[:80]}...'")
        
        answer = None
        for question_key, answer_value in EXAM_QA_MAP.items():
            if question_key in question_text:
                answer = answer_value
                break
        
        if not answer:
            print(f"⚠️  No answer found for: {question_text[:60]}...")
            return False
        
        print(f"      🎯 Looking for answer: '{answer}'")
        
        answer_labels = question_container.locator('label[data-testid^="exam-answer-"]')
        
        print(f"      📊 Primary selector found {answer_labels.count()} answer labels")
        
        using_fallback = False
        if answer_labels.count() == 0:
            print("      🔄 Using fallback selector for answer labels")
            answer_labels = question_container.locator('label.group.flex.w-fit.cursor-pointer.select-none.items-center.rounded-4.text-typeface-900.flex-row.gap-4.text-base')
            print(f"      📊 Fallback found {answer_labels.count()} answer labels")
            using_fallback = True
        
        for i in range(answer_labels.count()):
            try:
                label = answer_labels.nth(i)
                
                current_label_text = ""
                if using_fallback:
                    spans = label.locator('> span')
                    print(f"      🔍 Label {i+1} has {spans.count()} direct span children")
                    if spans.count() >= 2:
                        current_label_text = spans.nth(1).inner_text().strip()
                    else:
                        current_label_text = label.inner_text().strip()
                else:
                    answer_text_element = label.locator('span.flex span').last
                    current_label_text = answer_text_element.inner_text().strip()
                
                print(f"      📝 Label {i+1} text: '{current_label_text}'")
                
                if answer == current_label_text or answer in current_label_text:
                    print(f"   ✓ Selected: {answer}")
                    human_delay(0.5, 1.2)
                    label.click() 
                    human_delay(0.3, 0.8)
                    return True
            except Exception as e:
                print(f"      ❌ Error processing label {i+1}: {e}")
                continue
        
        print(f"      ⚠️  Could not find matching answer '{answer}' in labels")
        return False
        
    except Exception as e:
        print(f"      ❌ Exception in solve_exam_question: {e}")
        import traceback
        traceback.print_exc()
        return False


def do_activity_exam(page):
    """Complete exam activity."""
    try:
        print("\n📚 Navigating to activity page...")
        safe_goto(page, "https://exam.global-exam.com/library/trainings/exercises/492/activities")
        handle_cookies(page)
        human_delay(2, 4)
        
        activity_button_selector = 'button[data-testid="activity-button-1102"]'
        
        if page.locator(activity_button_selector).count() > 0:
            print("✅ Starting 'Entraînement 201'...")
            real_click(page, activity_button_selector)
            human_delay(2, 3)
        else:
            print("❌ Activity button not found")
            return False
        
        start_button_selector = 'button[data-testid="start-activity-button"]'
        
        if page.locator(start_button_selector).is_visible(timeout=5000):
            print("✅ Clicking 'Démarrer'...")
            real_click(page, start_button_selector)
            human_delay(2, 3)
        
        question_selector = 'div[data-testid^="question-"]'
        question_fallback_selector = '#question-wrapper'
        validate_button_selector = 'button:has-text("Valider")'
        validate_button_selector_2 = 'button:has-text("Passer")'
        validate_button_fallback_selector = 'button:has-text("Suivant")'
        finish_button_selector = 'button:has-text("Terminer")'
        finish_button_fallback_selector = 'button:has-text("Suivant")'
        
        total_questions_processed = 0
        page_number = 1
        activity_finished = False
        
        while not activity_finished:
            questions = page.locator(question_selector)
            total_on_page = questions.count()
            
            if total_on_page == 0:
                print(f"   🔄 Primary question selector found 0 questions, trying fallback...")
                questions = page.locator(question_fallback_selector)
                total_on_page = questions.count()
                print(f"   📊 Fallback selector found {total_on_page} questions")
            
            print(f"\n📄 Page {page_number} - Processing {total_on_page} questions...")

            for i in range(total_on_page):
                current_q = questions.nth(i)
                current_q.scroll_into_view_if_needed()
                print(f"📝 Question {i + 1}/{total_on_page}:", end=" ")
                solve_exam_question(page, current_q)
                human_delay(1, 2)
                total_questions_processed += 1

            human_delay(1, 2)
            
            print("\n🔍 Checking for finish button...")
            finish_button_visible = page.locator(finish_button_selector).is_visible(timeout=3000)
            print(f"   Primary finish button ('Terminer'): {finish_button_visible}")
            if not finish_button_visible:
                finish_button_visible = page.locator(finish_button_fallback_selector).is_visible(timeout=1000)
                print(f"   Fallback finish button ('Suivant'): {finish_button_visible}")
                if finish_button_visible:
                    print("   🔄 Using fallback finish button selector")
                    finish_button_selector = finish_button_fallback_selector
            
            if finish_button_visible:
                print("\n✅ Activity complete! Clicking 'Terminer'...")
                real_click(page, finish_button_selector)
                # wait for page to reload
                page.wait_for_load_state("domcontentloaded")
                human_delay(5, 5)
                if page_number != 6:
                    page_number += 1
                else:
                    activity_finished = True
            else:
                print("\n🔍 Checking for validate button...")
                validate_button_visible = page.locator(validate_button_selector).is_visible(timeout=3000)
                print(f"   Primary validate button ('Valider'): {validate_button_visible}")
                if not validate_button_visible:
                    validate_button_visible = page.locator(validate_button_fallback_selector).is_visible(timeout=1000)
                    print(f"   Fallback validate button ('Suivant'): {validate_button_visible}")
                    if validate_button_visible:
                        print("   🔄 Using fallback validate button selector")
                        validate_button_selector = validate_button_fallback_selector
                    else:
                        validate_button_visible = page.locator(validate_button_selector_2).is_visible(timeout=1000)
                        print(f"   Fallback validate button ('Passer'): {validate_button_visible}")
                        if validate_button_visible:
                            print("   🔄 Using fallback validate button selector")
                            validate_button_selector = validate_button_selector_2
                
                if validate_button_visible:
                    print("✅ Clicking 'Valider' - Moving to next page...")
                    real_click(page, validate_button_selector)
                    human_delay(2, 4)
                    page_number += 1
                else:
                    print("⚠️  No validation button found (neither primary nor fallback)")
                    break
        
        print(f"\n🎉 Activity finished! Total questions: {total_questions_processed} across {page_number} page(s)\n")
        return True
        
    except Exception as e:
        print(f"❌ Error during activity: {e}")
        return False




if __name__ == "__main__":
    with sync_playwright() as p:
        user_data_dir = "./browser_session"
        
        stealth_args = [
            "--disable-infobars",
            "--no-sandbox",
            "--no-first-run",
            "--hide-scrollbars",
            "--mute-audio",
            "--disable-background-networking",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-breakpad",
            "--disable-component-extensions-with-background-pages",
            "--disable-extensions",
            "--disable-features=TranslateUI",
            "--disable-ipc-flooding-protection",
            "--disable-renderer-backgrounding",
            "--enable-features=NetworkService,NetworkServiceInProcess",
            "--force-color-profile=srgb",
        ]

        browser_context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            args=stealth_args,
            ignore_default_args=["--enable-automation"],
            device_scale_factor=2,
            has_touch=False,
            is_mobile=False,
            locale="fr-FR",
            timezone_id="Europe/Paris"
        )
        
        page = browser_context.pages[0]

        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            
            const mockPlugins = [
                { name: "PDF Viewer", filename: "internal-pdf-viewer", description: "Portable Document Format" },
                { name: "Chrome PDF Viewer", filename: "internal-pdf-viewer", description: "Portable Document Format" },
                { name: "Chromium PDF Viewer", filename: "internal-pdf-viewer", description: "Portable Document Format" },
                { name: "Microsoft Edge PDF Viewer", filename: "internal-pdf-viewer", description: "Portable Document Format" },
                { name: "WebKit built-in PDF", filename: "internal-pdf-viewer", description: "Portable Document Format" }
            ];
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const p = [...mockPlugins];
                    p.refresh = () => {};
                    p.item = (i) => p[i];
                    p.namedItem = (name) => p.find(x => x.name === name);
                    return p;
                },
            });
            Object.defineProperty(navigator, 'mimeTypes', {
                get: () => {
                    const m = [{ type: 'application/pdf', suffixes: 'pdf', description: '', enabledPlugin: mockPlugins[0] }];
                    m.item = (i) => m[i];
                    m.namedItem = (name) => m.find(x => x.type === name);
                    return m;
                }
            });

            Object.defineProperty(navigator, 'languages', {
                get: () => ['fr-FR', 'fr', 'en-US', 'en'],
            });

            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: 'denied', onchange: null }) :
                originalQuery(parameters)
            );
            
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel(R) Iris(R) Plus Graphics 640'; 
                }
                return getParameter.apply(this, [parameter]);
            };

            if (Object.keys(localStorage).length === 0) {
                 localStorage.setItem('theme', 'light');
                 localStorage.setItem('hasVisited', 'true');
                 localStorage.setItem('preferred_language', 'fr');
                 localStorage.setItem('cookie_consent', 'true');
            }
        """)

        print("🚀 Starting Global Exam automation...\n")
        page.goto("https://auth.global-exam.com/login", wait_until="networkidle")
        handle_cookies(page)

        if "login" in page.url:
            print("🔐 Logging in...")
            human_delay(1, 2)
            page.locator("[name='email']").click()
            page.keyboard.type(EMAIL, delay=random.randint(50, 150))
            
            human_delay(0.5, 1)
            
            page.locator("[name='password']").click()
            page.keyboard.type(PASSWORD, delay=random.randint(50, 150))
            
            human_delay(1, 2)
            real_click(page, "button[type='submit']")
            page.wait_for_load_state("networkidle")
            print("✅ Login successful\n")
            choose_ipssi(page)
        else:
            print("✅ Already logged in\n")

        choose_ipssi(page)

        print("\n🔄 Starting activity loop...\n")
        while True:
            do_activity_exam(page)
            print("🔄 Returning to home page...")
            safe_goto(page, "https://exam.global-exam.com/")
            human_delay(2, 4)

        browser_context.close()
