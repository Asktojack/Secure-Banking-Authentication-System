def detect_device(user_agent):

    platform = (user_agent.platform or "").lower()
    browser = (user_agent.browser or "").lower()

    # Device
    if "windows" in platform:
        device = "Windows PC"

    elif "android" in platform:
        device = "Android Phone"

    elif "iphone" in platform or "ios" in platform:
        device = "iPhone"

    elif "mac" in platform:
        device = "Mac"

    elif "linux" in platform:
        device = "Linux"

    else:
        device = "Unknown Device"

    # Browser
    if "chrome" in browser:
        browser_name = "Google Chrome"

    elif "edge" in browser:
        browser_name = "Microsoft Edge"

    elif "firefox" in browser:
        browser_name = "Mozilla Firefox"

    elif "safari" in browser:
        browser_name = "Safari"

    else:
        browser_name = "Unknown Browser"

    return device, browser_name