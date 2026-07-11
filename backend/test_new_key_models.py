import google.generativeai as genai

api_key = "AQ.Ab8RN6KplbwgkX3LtdJyt47UcK4HTQ0X4QPIpJ1tJlE0yNlS_w"
genai.configure(api_key=api_key)

models_to_test = [
    "gemini-2.5-flash",
    "gemini-2.0-flash-exp",
    "gemini-2.0-flash-lite-preview-02-05",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-pro-exp-02-05",
    "gemini-3.5-flash",
]

for model_name in models_to_test:
    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=100,
                response_mime_type="application/json",
            )
        )
        response = model.generate_content("Reply with JSON: {\"status\": \"ok\"}")
        print(f"✅ {model_name}: WORKS - {response.text[:50]}")
    except Exception as e:
        print(f"❌ {model_name}: {str(e)[:150]}")
