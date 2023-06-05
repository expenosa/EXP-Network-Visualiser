import os
import gradio as gr

def update(name):
    return f"Welcome to Gradio, {name}!"

# with gr.Blocks() as demo:
#     gr.Markdown("Start typing below and then click **Run** to see the output.")
#     with gr.Row():
#         inp = gr.Textbox(placeholder="What is your name?")
#         out = gr.Textbox()
#     btn = gr.Button("Run")
#     btn.click(fn=update, inputs=inp, outputs=out)

with open('foggate.html') as f:
    html_data = f.read()

with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("Start typing below and then click **Run** to see the output.")
            text1 = gr.Textbox(label="From Node")
            text2 = gr.Textbox(label="To Node")
            btnA = gr.Button("Add")
        with gr.Column(scale=9):
            gr.HTML(html_data)

demo.launch(inline=True, inbrowser=True)