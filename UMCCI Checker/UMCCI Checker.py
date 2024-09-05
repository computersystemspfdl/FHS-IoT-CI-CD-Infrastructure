from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
import time
from openai import OpenAI

def class_to_html_tag(class_name):
    
    mapping = {
        'android.widget.Button': 'button',
        'android.widget.TextView': 'span',
        'android.widget.EditText': 'input',
        'android.widget.ImageView': 'img',
        'android.view.ViewGroup': 'div',
        'android.widget.CheckBox': 'input type="checkbox"',
        'android.widget.RadioButton': 'input type="radio"',
        'android.widget.ListView': 'ul',
        'android.widget.LinearLayout': 'div',
        'android.widget.RelativeLayout': 'div'
    }
    return mapping.get(class_name, 'div')  

def print_activity_and_elements(driver, description="Details of current screen:"):
    
    current_activity = driver.current_activity
    print(f'[#]{description} {current_activity}')
    
    elements = driver.find_elements(AppiumBy.XPATH, "//*[@clickable='true']")
    #print(elements)
    for element in elements:
        element_id = element.get_attribute('resource-id')
        element_class = element.get_attribute('class')
        element_text = element.get_attribute('text')
        element_clickable = element.get_attribute('clickable')
        #print(f'Element ID: {element_id}, Element Class: {element_class}, Element Text: {element_text}')
        tag_name = class_to_html_tag(element_class)
        print(f'<{tag_name} id="{element_id}" class="{element_class}" text="{element_text}"> clickable="{element_clickable}"')

def query_gpt(prompt):
    # print(prompt)
    client = OpenAI(
        #api_key=os.environ['APIKey']
        api_key="***",
        base_url="***"
    )
    retry = 0
    completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", "text": prompt
                    },
                ],
            }
        ],
        model="gpt-4o-mini-2024-07-18",
        timeout=30
    )
    #print(completion)
    res = completion.choices[0].message.content
    return res

def sort_elements(elements):
    element_list = []
    
    for element in elements:
        element_id = element.get_attribute('resource-id')
        element_class = element.get_attribute('class')
        element_text = element.get_attribute('text')
        element_clickable = element.get_attribute('clickable')
        tag_name = class_to_html_tag(element_class)
        #print(f'<{tag_name} id="{element_id}" class="{element_class}" text="{element_text}"> clickable="{element_clickable}"')
        element_list.append(f'<{tag_name} id="{element_id}" class="{element_class}" text="{element_text}"> clickable="{element_clickable}"')
    
    prompt = '''
    You are a smartphone assistant to help users complete tasks by interacting with mobile apps related to IoT control based on the Matter protocol (just like Tuya Smart, Google Home, Amazon Alexa and so on). Your task is to cooperate in the depth-first exploration of the app page elements. The order of exploration of the elements on the page is sorted according to importance, with important elements at the front. 
    
    Given a list containing all elements of the current UI page, your job is to reorder the list based on your prediction of the importance of each element in the list. At the same time, you should pay attention that when you analyze that the element may be a return, back page, exit, or similar operation, put such operations at the end to reduce invalid exploration such as exiting the page too early. Likewise, if you find specific device names or device icons related elements, put them in the front position for exploration.
    
    Your answer must always be one element per line, without numbering (just like the list of elements given to you each time). Your answer may not contain any explanatory text. The number of elements you output must match the number of elements in the original list given to you. You cannot omit elements or modify the content of elements.
    
    The list of elements is as follows:
    
    '''
    for i in element_list:
        prompt = prompt + i +'\n'
    gpt_res = query_gpt(prompt)
    print(gpt_res)
    sorted_element_list = gpt_res.strip().split('\n')
    element_dict = {f'<{class_to_html_tag(element.get_attribute("class"))} id="{element.get_attribute("resource-id")}" class="{element.get_attribute("class")}" text="{element.get_attribute("text")}"> clickable="{element.get_attribute("clickable")}"': element for element in elements}
    sorted_elements = [element_dict[element] for element in sorted_element_list if element in element_dict]
    print(sorted_elements)
    return sorted_elements

def explore_elements(driver, visited_activities, depth=0):
    current_activity = driver.current_activity
    print(f"{'  ' * depth}Exploring Activity: {current_activity} at depth {depth}")

    if current_activity not in visited_activities:
        visited_activities[current_activity] = []

    #print(driver.page_source)

    elements = driver.find_elements(AppiumBy.XPATH, "//*[@clickable='true']")
    for index in range(len(elements)):
        elements = driver.find_elements(AppiumBy.XPATH, "//*[@clickable='true']") 
        #print_activity_and_elements(driver, "Details of new screen:")
        elements = sort_elements(elements)

        if index >= len(elements):
            continue
        element = elements[index]

        if element.is_displayed() and element.is_enabled():
            element_text = element.get_attribute('text') or "No Text"
            if "删除" in element_text or "解绑" in element_text or "移除" in element_text:
                print(f"{'  ' * depth}Skipping Element {index}: ID={element.get_attribute('resource-id')}, Text={element_text}")
                continue

            if index in visited_activities[current_activity]:
                continue  
            
            # if element.get_attribute('clickable')=='false':
            #     print(f"{'  ' * depth}Skipping Element {index}: clickable='false'")
            #     visited_activities[current_activity].append(index)  
            #     continue

            if element.get_attribute('content-desc')=="toolbar_navigation":
                print(f"{'  ' * depth}Skipping Element {index}: NO Back")
                visited_activities[current_activity].append(index) 
                continue


            visited_activities[current_activity].append(index)  
            print(f"{'  ' * depth}Clicking Element {index}: ID={element.get_attribute('resource-id')}, Text={element_text}, class={element.get_attribute('class')}")
            element.click()
            time.sleep(2)  

            new_activity = driver.current_activity
            if new_activity != current_activity:
                if new_activity in visited_activities:
                    print("No back!")
                explore_elements(driver, visited_activities, depth + 1)
                print(f"{'  ' * depth}Returning to Activity: {current_activity} at depth {depth}")
                driver.back()
                time.sleep(2)  

def main():
    capabilities = {
        'platformName': 'Android',
        'automationName': 'uiautomator2',
        'deviceName': 'Android',
        'app': 'C:\\Users\\whqxb\\Downloads\\AutoDroid-newbranch\\scripts\\apks\\tuya.apk',
        'noReset': True
    }
    appium_server_url = 'http://localhost:4723'
    options = UiAutomator2Options().load_capabilities(capabilities)
    driver = webdriver.Remote(command_executor=appium_server_url, options=options)
    
    try:
        visited_activities = {} 
        door_element = 'a'

        target_element = driver.find_element(AppiumBy.ID, 'com.tuya.smartiot:id/deviceName')
        if target_element.get_attribute('class') == 'android.widget.TextView' and \
           target_element.get_attribute('text') == 'WiZ A19':
            target_element.click()
            print("[#]Enter to WiZ A19.") 
        
        explore_elements(driver, visited_activities)
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
