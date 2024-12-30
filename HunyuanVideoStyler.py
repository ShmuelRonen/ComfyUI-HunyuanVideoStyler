import json
import pathlib
from collections import defaultdict

class Template:
    def __init__(self, prompt, negative_prompt, **kwargs):
        self.prompt = prompt
        self.negative_prompt = negative_prompt

    def replace_prompts(self, positive_prompt, negative_prompt):
        positive_result = self.prompt.replace('{prompt}', positive_prompt)
        negative_result = ', '.join(x for x in (self.negative_prompt, negative_prompt) if x)
        return positive_result, negative_result

class StylerData:
    def __init__(self, datadir=None):
        self._data = defaultdict(dict)
        if datadir is None:
            datadir = pathlib.Path(__file__).parent / 'data'

        # Add "None" option to each category
        none_template = Template("", "")
        
        for j in datadir.glob('*/*.json'):
            try:
                with j.open('r') as f:
                    content = json.load(f)
                    group = j.parent.name
                    # Add None as first option
                    self._data[group]["None"] = none_template
                    # Add all other templates
                    for template in content:
                        self._data[group][template['name']] = Template(**template)
            except Exception as e:
                print(f"Warning: Error loading {j}: {e}")

    def __getitem__(self, item):
        return self._data[item]

    def keys(self):
        return self._data.keys()
        
styler_data = StylerData()

class HunyuanVideoStyler:
    # Class attributes for ComfyUI
    RETURN_TYPES = ('STRING', 'STRING',)
    RETURN_NAMES = ('text_positive', 'text_negative',)
    FUNCTION = 'style_video_prompt'
    CATEGORY = 'conditioning/video'
    
    style_order = [
        'movie_scenes',  # 1. Base movie scene reference
        'timeofday',     # 2. Base environment - time
        'weather',       # 3. Base environment - conditions
        'lighting',      # 4. Light setup
        'shooting',      # 5. Basic shooting approach
        'camera',        # 6. Camera specifics
        'composition',   # 7. Composition rules
        'effects',       # 8. Special effects
        'video_styles'   # 9. Overall style
    ]

    @classmethod
    def INPUT_TYPES(cls):
        menus = {}
        # Create menu options with "None" as first choice
        for menu in cls.style_order:
            options = list(styler_data[menu].keys())
            if "None" in options:
                options.remove("None")
                options = ["None"] + sorted(options)
            menus[menu] = (options,)
        
        return {
            "required": {
                "text_positive": ("STRING", {"default": "", "multiline": True}),
                "text_negative": ("STRING", {"default": "", "multiline": True}),
                **menus,
                "debug_prompt": ("BOOLEAN", {"default": False, "label": "Show Prompt Building"})
            }
        }

    def style_video_prompt(self, text_positive, text_negative, debug_prompt, **kwargs):
        positive_result = text_positive
        negative_result = text_negative
        
        for menu in self.style_order:
            if menu in kwargs and kwargs[menu] and kwargs[menu] != "None":
                style = styler_data[menu][kwargs[menu]]
                positive_result, negative_result = style.replace_prompts(
                    positive_result, negative_result
                )

                if debug_prompt:
                    print(f"\nAfter applying {menu} - {kwargs[menu]}:")
                    print(f"Positive: {positive_result}")
                    print(f"Negative: {negative_result}")

        return (positive_result, negative_result)

# Node class mapping for ComfyUI
NODE_CLASS_MAPPINGS = {
    "HunyuanVideoStyler": HunyuanVideoStyler
}

# Display names for the UI
NODE_DISPLAY_NAME_MAPPINGS = {
    "HunyuanVideoStyler": "Hunyuan Video Styler"
}