from flask import Flask, request, render_template, redirect,url_for
from dotenv import load_dotenv
from openai import OpenAI
from ollama import chat
from pyngrok import ngrok,conf
import json
import os

backend = Flask(__name__)

@backend.route('/',methods=['GET','POST'])
def home():
    return render_template('solo leveling.html')

def model(prompt):
    api = os.getenv('API_KEY')
    client = OpenAI(
        api_key=api,
        base_url="https://api.groq.com/openai/v1",
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages = [{
            'role':'system',
            'content':"""You are an AI that creates a gamified "Solo Leveling" style progression system.

         Rules:
         - Output ONLY valid JSON
         - No explanation, no extra text 
         - only resource for leraning included in json
         - No markdown

         Create exactly 5 levels.

         Each level must include:
         - Learning_Resource
         - level_number
         - level_name
         - description
         - total_xp_required
         - tasks (3 tasks)

         Each task must include:
         - task_name
         - difficulty (easy, medium, hard)
         - xp_reward

         XP rules:
         - easy: 10 XP
         - medium: 20 XP
         - hard: 50 XP

         STRICT: Output must be valid JSON only."""
        },
        {
         'role':'user',
         'content':f'{prompt}'}
         ],
        # temperature=0.2
        )
    content = response.choices[0].message.content

    data = json.loads(content)
    with open('level.json','w') as f:
        json.dump(data,f)


@backend.route('/new_goal', methods=['GET','POST'])
def new_goal():
    if request.method == 'POST':
        goal = request.form.get('goal')
        model(goal)
        return redirect(url_for('show_task'))

    return render_template('new_goal.html')


def dataa():
    try:
        with open('level.json','r') as f:
            content = json.load(f)
        return content
    except FileNotFoundError:
        return []
    


@backend.route('/show_task',methods=['GET','POST'])
def show_task():
    data = dataa()
    completes = complete()
    skips = skip()

    pending = pending_data()

    pending_names = [task["task_name"] for task in pending]


    if request.method == 'POST':
        action = request.form.get('action')
        task_name = request.form.get('task_name')
        difficulty = request.form.get('difficulty')
        xp_reward = int(request.form.get('xp_reward'))

        if action == 'yes':
            try:
                with open('xp.txt', 'r') as f:
                    current_xp = int(f.read())
            except:
                current_xp = 0

            new_xp = current_xp + xp_reward
            with open('xp.txt', 'w') as f:
                f.write(str(new_xp))

            completed = complete()
            completed.append(task_name)
            with open('complete.txt', 'w') as f:
                json.dump(completed, f)

            return redirect(url_for('show_task'))

        elif action == 'no':

            try:
                with open('pending.json', 'r') as f:
                    content = f.read().strip()
                    pending = json.loads(content) if content else []

            except FileNotFoundError:
                pending = []

            pending.append({
                'task_name': task_name,
                'difficulty': difficulty,
                'xp_reward': xp_reward
            })

            with open('pending.json', 'w') as f:
                json.dump(pending, f)

            return redirect(url_for('show_task'))
        
        elif action == 'skip':
            
            try:
                with open('xp.txt', 'r') as f:
                    current_xp = int(f.read())
            except FileNotFoundError:
                current_xp = 0
            if current_xp < 20:
                # re-render with error message
                data = dataa()
                return render_template('show_task.html',
                    levels=data['levels'],
                    error='Not enough XP to skip. Need 20 XP.')
            
            new_xp = current_xp - 20
            with open('xp.txt', 'w') as f:
                f.write(str(new_xp))
            
            skiped = skip()
            skiped.append(task_name)
            with open('skip.txt','w') as f:
                json.dump(skiped,f)
            
            return redirect(url_for('show_task'))

        elif action == 'quit':
            return render_template('solo leveling.html')

    # GET request or after handling POST — show all levels and tasks

    levels = None
    tasks = None
    difficultys = None

    if data is None:
        return redirect(url_for('new_goal'))
    else:
        for lvl in data["levels"]:
            for t in lvl["tasks"]:
                if (t["task_name"] not in completes and
                    t["task_name"] not in pending_names and 
                    t["task_name"] not in skips):
                    levels = lvl
                    tasks = t
                    difficultys = t['difficulty']
                    break

            if tasks:
                break
        else:
            files = ['complete.txt','skip.txt','level.json']

            for i in files:
                try:
                    os.remove(i)
                except FileNotFoundError:
                    pass
            return render_template('final.html')

    return render_template(
    "show_task.html",
    levels=levels,
    tasks=tasks,
    difficulty = difficultys
    )

def pending_data():
    try:
        with open('pending.json','r') as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except FileNotFoundError:
        return []

def pending_complete():
        try:
            with open('pending_complete.txt','r') as f:
                content = json.load(f)
            return content
        except FileNotFoundError:
            return []

def pending_skip():
    try:
        with open('pending_skip.txt','r') as f:
                content = json.load(f)
        return content
    except FileNotFoundError:
        return []
        
@backend.route('/pending_task',methods=['GET','POST'])
def pending_task():
    p_s = pending_skip()
    p_c = pending_complete()

    ddata = pending_data()

    if request.method == 'POST':
        action = request.form.get('action')
        task_name = request.form.get('task_name')
        difficulty = request.form.get('difficulty')
        xp_reward = int(request.form.get('xp_reward'))


        if 'yes' == action:

            a = xp_reward
            # clean = ddata.pop(ind)
            with open('xp.txt', 'r') as f:
                x = int(f.read())
            n = x + a
            print(f'complete: {n}')
            with open('xp.txt','w') as f:
                f.write(str(n))
            with open('pending.json','w') as f:
                json.dump(ddata,f)

            pending = pending_complete()
            pending.append(task_name)
            with open('pending_complete.txt','w') as f:
                json.dump(pending,f)
            
            return redirect(url_for('pending_task'))
        
        elif 'no' == action:
            
            c = xp_reward
            with open('xp.txt', 'r') as f:
                l = int(f.read())
            o = l - c
            print(f'incomplete: {o}')
            with open('xp.txt','w') as f:
                f.write(str(o))

            pending_skips = pending_skip()
            pending_skips.append(task_name)
            with open('pending_skip.txt','w') as f:
                json.dump(pending_skips,f)

            return redirect(url_for('pending_task'))
        
        elif 'quit' == action:
            return redirect(url_for('home'))
        

    tasks = None
    ind = None

    for indx,tk in enumerate(list(ddata)):
        if (tk["task_name"] not in p_s and
            tk["task_name"] not in p_c):
            # clean = ddata.pop(ind)
            ind = indx
            tasks = tk
            break
    else:
        files = ['pending_complete.txt','pending_skip.txt','pending.json']
        for i in files:
            try:
                os.remove(i)
            except FileNotFoundError:
                pass
        return render_template('final.html')
    
    return render_template('pending_task.html',
                           tasks = tasks)


def complete():
    try:
        with open('complete.txt','r') as f:
            content = json.load(f)
        return content
    except FileNotFoundError:
        return []
def skip():
        try:
            with open('skip.txt','r') as f:
                content = json.load(f)
            return content
        except FileNotFoundError:
            return []

conf.get_default().auth_token='3Ga0kzoko9TRMvUZOzCWgV9iiNz_51DugyUD4sDdCzxrRJFcd'

tunnels = ngrok.get_tunnels()
print(f'Active tunnels: {tunnels}')
for tunnel in tunnels:
    print(f'Closing: {tunnel.public_url}')
    ngrok.disconnect(tunnel.public_url)

ngrok.kill()
print('All tunnels closed')
if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        public_url = ngrok.connect(5000)
        print(f'Open this on your phone: {public_url}')
    
    backend.run(debug=True, port=5000)