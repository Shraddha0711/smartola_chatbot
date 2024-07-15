import google.generativeai as genai
import os
from dotenv import load_dotenv
from prompt import Prompt
import chainlit as cl
import mysql.connector
import pandas as pd
import plotly.graph_objects as go
import re
from dwnldcsv import setup_and_run_flask


load_dotenv()
client=genai.configure(api_key=os.getenv('gemini_api_key'))
model = genai.GenerativeModel('gemini-pro',generation_config={'temperature':0.4})

prompt1 = [{'role': 'user', 'parts': [f'{Prompt}']},
            {'role': 'model', 'parts': ["Understood"]}]

chat = model.start_chat(history=prompt1)    

def genai2(input_message):        
    '''
    "generationConfig": {"temperature": 0.4,"topP":0.5,"topK": 3,"candidateCount": 1,"maxOutputTokens": 2600}
    '''
    response = chat.send_message(input_message)
    return response.text
    
def query_database(query):

    conn = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database'))

    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    columns = [description[0] for description in cur.description] if cur.description else []
    conn.close()
    return rows, columns


@cl.on_message
async def main(message: cl.Message):
    # await cl.Avatar(
    #         name="Smartola",
    #         url="https://img.freepik.com/free-vector/chatbot-chat-message-vectorart_78370-4104.jpg?w=740&t=st=1720692917~exp=1720693517~hmac=6ce016d0f1a487787d7f9c9df7c6a0140882bbcc4859ecb35bddcc9df0e4ce9a",
    #     ).send()
    res=genai2(message.content)
    if "```sql" in res:
        query = (((res.split("```"))[1]).removeprefix("sql\n")).removesuffix("\n")
        key_words = r"\b(DELETE|UPDATE|INSERT|CREATE|TRUNCATE|SET)\b"
        if re.search(key_words, query, flags=re.IGNORECASE):      
            msg = "I am sorry, I am unable to modify the existing database. I am an AI chatbot designed to analyze data from the Rewardola platform and can only provide insights based on user quesions.If you need to modify data, you can use the appropriate database management tools or consult with a database administrator."  
            await cl.Message(content=msg,author="Smartola").send()
        else:
            rows,columns=query_database(query)
            df=pd.DataFrame(rows,columns=columns)   
            
            if len(rows) == 0 :
                await cl.Message(content=f"{res}\n\n**Count : {len(rows)}**").send()   
            elif len(rows)==1 and len(columns)==1:    
                await cl.Message(content=f"{res}\n\n\n **The answer is : {rows[0][0]}**",author="Smartola").send()  
            else:
                fig = go.Figure(data=[go.Table(
                    header=dict(values=list(df.columns),
                                line_color='black',
                                align="left"),
                    cells=dict(values=[df[i] for i in df.columns],
                               fill_color='white',line_color='black',
                               align="left"))],layout=dict(autosize=True))
                fig.update_layout(autosize=False,
                                  width=800,
                                  height=400,
                                  margin=dict(l=10,r=10,t=10,b=10))
                await cl.Message(content=f"{res}\n\n**Count : {len(rows)}**", elements=[cl.Plotly(name="chart", figure=fig, display="inline")],author="Smartola").send()
                setup_and_run_flask(df)
                await cl.Message(content=f"**Download the data as CSV**[ file](http://192.168.43.38:5000/download_csv)", author="Smartola").send()
                
    else:
        await cl.Message(content=res,author="Smartola").send()
