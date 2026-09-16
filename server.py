import os, base64, tempfile
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def save_data_url(data):
    header, encoded = data.split(",", 1)
    ext = ".png" if "png" in header else ".jpg"
    f = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    f.write(base64.b64decode(encoded))
    f.close()
    return f.name

@app.post("/generate")
def generate():
    data = request.get_json()
    character = save_data_url(data["character"])
    styles = [save_data_url(x) for x in data.get("styles", [])[:15]]

    prompt = """Create a fresh original character illustration.
The first reference image is the character reference. Preserve its recognizable
character design and important visual features.
The remaining images are style references. Use their general visual characteristics
such as line quality, coloring, shading, proportions, and rendering approach.
Do not copy a reference composition. Create a new illustration.
"""
    if data.get("request"):
        prompt += "\nUser request: " + data["request"]
    prompt += "\nCharacter preservation: " + data.get("preserve", "높음")

    handles=[]
    try:
        for p in [character]+styles:
            handles.append(open(p,"rb"))
        result=client.images.edit(
            model="gpt-image-2",
            image=handles,
            prompt=prompt,
            input_fidelity="high",
            quality="medium",
            size="1024x1024",
            output_format="png"
        )
        image="data:image/png;base64,"+result.data[0].b64_json
        return jsonify({"image":image})
    finally:
        for h in handles: h.close()
        for p in [character]+styles:
            try: os.remove(p)
            except: pass

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",7860)))
