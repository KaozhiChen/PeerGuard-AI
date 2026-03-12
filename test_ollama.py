import requests

def test_local_ollama():
    url = "http://localhost:11434/api/generate"

    payload = {
        "model": "qwen3:8b",
        "prompt": "Hello, who are you?",
        "stream": False
    }

    print("Sending request to local ollama...")

    try: 
        response = requests.post(url, json = payload)

        if response.status_code == 200:
            print("Response received from local ollama!")
            res = response.json()

            print ("\n--- fully generated response ---")
            print(res)

            print("\n--- response tokens ---")
            print(res.get("response"))  

        else:
            print(f"Error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("Could not connect to local ollama. Is it running?")
    

if __name__ == "__main__":
    test_local_ollama()