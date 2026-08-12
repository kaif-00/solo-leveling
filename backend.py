from flask import Flask, request, render_template, redirect,url_for,session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from pyngrok import ngrok,conf
from openai import OpenAI
import json
import os
import re


backend = Flask(__name__)
# with this line we are connecting the database with the flask app and we are using sqlite database
backend.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///User.db'
backend.config['SECRET_KEY'] = 'secretkey'
db = SQLAlchemy(backend)


class User(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(35),nullable=False, unique=True)
    password = db.Column(db.String(80),nullable=False)

with backend.app_context():
    db.create_all()

def user_folder():
    user = session.get('username')
    if not user:
        return None

    path = f'data/{user}'
    os.makedirs(path, exist_ok = True)
    return path

def dataa():
    try:
        folder = user_folder()
        with open(f'{folder}/level.json','r') as f:
            content = json.load(f)
        return content
    except FileNotFoundError:
        return None

def get_question_level():
    try:
        folder = user_folder()
        with open(f'{folder}/question.txt','r') as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except FileNotFoundError:
        return []

def write_question_level(lvl_num):
    qust = get_question_level()
    folder = user_folder()

    if lvl_num not in qust:
        qust.append(lvl_num)
    with open(f'{folder}/question.txt','w') as f:
        json.dump(qust,f)


def answered_question():
    try:
        folder = user_folder()
        with open(f'{folder}/answered.txt', 'r') as f:
            content = f.read().strip()
        return json.loads(content) if content else []
    except FileNotFoundError:
        return []

def remove_file(files):
    folder = user_folder()
    for f in files:
        try:
            os.remove(f'{folder}/{f}')
        except FileNotFoundError:
            pass

def complete():
    try:
        folder = user_folder()
        with open(f'{folder}/complete.txt','r') as f:
            content = json.load(f)
        return content
    except FileNotFoundError:
        return []

def skip():
        try:
            folder = user_folder()
            with open(f'{folder}/skip.txt','r') as f:
                content = json.load(f)
            return content
        except FileNotFoundError:
            return []

def pending_data():
    try:
        folder = user_folder()
        with open(f'{folder}/pending.json','r') as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except FileNotFoundError:
        return []

def pending_complete():
        try:
            folder = user_folder()
            with open(f'{folder}/pending_complete.txt','r') as f:
                content = f.read().strip()
            return json.loads(content) if content else []
        except FileNotFoundError:
            return []

def pending_skip():
    try:
        folder = user_folder()
        with open(f'{folder}/pending_skip.txt','r') as f:
                content = f.read().strip()
        return json.loads(content) if content else []
    except FileNotFoundError:
        return []



@backend.route('/',methods=['GET','POST'])
def index():
    return render_template('index.html')


@backend.route('/sign_up',methods=['GET','POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        existing = User.query.filter_by(username = username).first()

        if existing :
            return render_template('sign_up.html', error = 'Username already exists')

        hashed = generate_password_hash(password)
        new_user = User(username = username, password = hashed)
        db.session.add(new_user)
        db.session.commit()

        os.makedirs(f'data/{username}', exist_ok=True)
        session['username'] = username
        return redirect(url_for('home'))
    
    return render_template('sign_up.html')


@backend.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        existing = User.query.filter_by(username = username).first()

        if not existing or not check_password_hash(existing.password,password):
            return render_template('login.html', error = 'If you are new user please sign up first or check your username and password')
        
        session['username'] = username
        return redirect(url_for('home'))
    
    return render_template('login.html')


@backend.route('/home',methods=['GET','POST'])
def home():
    return render_template('solo leveling.html')


def model(prompt):
    folder = user_folder()
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
         -levels
            - learning_Resource
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
    with open(f'{folder}/level.json','w') as f:
        json.dump(data,f)

@backend.route('/new_goal', methods=['GET','POST'])
def new_goal():
    if request.method == 'POST':
        goal = request.form.get('goal')
        model(goal)
        return redirect(url_for('show_task'))

    return render_template('new_goal.html')


@backend.route('/show_task',methods=['GET','POST'])
def show_task():
    folder = user_folder()
    data = dataa()
    skips = skip()
    completes = complete()
    pending = pending_data()
    question_levels = get_question_level()

    pending_names = [task["task_name"] for task in pending]


    if request.method == 'POST':
        action = request.form.get('action')
        task_name = request.form.get('task_name')
        difficulty = request.form.get('difficulty')
        xp_reward = int(request.form.get('xp_reward'))

        if action == 'yes':
            try:
                folder = user_folder()
                with open(f'{folder}/xp.txt', 'r') as f:
                    current_xp = int(f.read())
            except:
                current_xp = 0

            new_xp = current_xp + xp_reward
            with open(f'{folder}/xp.txt', 'w') as f:
                f.write(str(new_xp))

            completed = complete()
            completed.append(task_name)
            with open(f'{folder}/complete.txt', 'w') as f:
                json.dump(completed, f)

            return redirect(url_for('show_task'))

        elif action == 'no':

            try:
                with open(f'{folder}/pending.json', 'r') as f:
                    content = f.read().strip()
                    pending = json.loads(content) if content else []

            except FileNotFoundError:
                pending = []

            pending.append({
                'task_name': task_name,
                'difficulty': difficulty,
                'xp_reward': xp_reward
            })

            with open(f'{folder}/pending.json', 'w') as f:
                json.dump(pending, f)

            return redirect(url_for('show_task'))
        
        elif action == 'skip':
            
            try:
                with open(f'{folder}/xp.txt', 'r') as f:
                    current_xp = int(f.read())
            except FileNotFoundError:
                current_xp = '0'
            if current_xp < 20:
                # re-render with error message
                data = dataa()
                return render_template('show_task.html',
                    levels=data['levels'],
                    error='Not enough XP to skip. Need 20 XP.')
            
            new_xp = current_xp - 20
            with open(f'{folder}/xp.txt', 'w') as f:
                f.write(str(new_xp))
            
            skiped = skip()
            skiped.append(task_name)
            with open(f'{folder}/skip.txt','w') as f:
                json.dump(skiped,f)
                
            return redirect(url_for('show_task'))

        elif action == 'quit':
            return render_template('solo leveling.html')

    # GET request or after handling POST — show all levels and tasks
    
    levels = None
    tasks = None
    difficultys = None
    resource = None

    if data is None:
        return redirect(url_for('new_goal'))
    
    else:
        for lvl in data["levels"]:
            lvl_tasks = lvl['tasks']
            resource = lvl['learning_Resource']

            all_done = all(                     #so this checks if all tasks are completed
                                                #if any task remain then the if condition fails and it goes 
                t["task_name"] in completes or  #to the second loop and continue with task showing process
                t["task_name"] in pending_names or #but if condition is true mean all task is completed for  
                t["task_name"] in skips            #the level then it shows the question page.
                for t in lvl_tasks
            )

            if not all_done:

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
                if lvl['level_number'] not in question_levels:
                    if not os.path.exists(f'{folder}/question.json'):
                        api = os.getenv('API_KEY')
                        client = OpenAI(
                            api_key=api,
                            base_url="https://api.groq.com/openai/v1",
                        )

                        response = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{
                                'role': 'system',
                                'content': """You generate quiz questions. Output ONLY valid JSON, no markdown.
                                Return exactly 3 questions as a simple list of strings.
                                Example output: ["question 1", "question 2", "question 3"]
                                STRICT: Output must be valid JSON only."""
                            }, {
                                'role': 'user',
                                'content': f'Generate 3 quiz questions for this level: {lvl["level_name"]} - {lvl["description"]} - {lvl['tasks']}'
                            }]
                        )
                        content = response.choices[0].message.content
                        datas = json.loads(content)
                        with open(f'{folder}/question.json','w') as f:
                            json.dump(datas,f)
                        # current_lvl += 1
                    return redirect(url_for('show_question'))
                continue

        else:
            folder = user_folder()
            files = ['complete.txt','skip.txt','question.json','question.txt','level.json']
            remove_file(files)
            return render_template('final.html')

        try:
            with open(f'{folder}/xp.txt','r') as f:
                content = f.read()
        except FileNotFoundError:
            content = '0'

        return render_template(
        "show_task.html",
        Learning_Resource = resource,
        levels=levels,
        tasks=tasks,
        difficulty = difficultys,
        content = content
        )


@backend.route('/question',methods=['GET','POST'])
def show_question():
    folder = user_folder()
    answered = answered_question()
    data = dataa()
    completes = complete()
    question_levels = get_question_level()
    pending = pending_data()                              # ← add
    pending_names = [task["task_name"] for task in pending]  # ← add
    skips = skip()  

    if request.method == 'POST':
        question = request.form.get('question')
        answer = request.form.get('answer','').strip()

        if not answer:
            return render_template('question.html', question=question, error='Answer cannot be empty.')

        api = os.getenv('API_KEY')
        client = OpenAI(
            api_key=api,
            base_url="https://api.groq.com/openai/v1",
        )

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                'role': 'system',
                'content': f"""Check this answer and give only a mark out of 100, no explanation.NO extra words only mark will be there
                Question: {question}
                Answer: {answer}"""
            }]
        )

        content = response.choices[0].message.content
        with open(f'{folder}/mark.txt','w') as f:
            f.write(str(content))

        with open(f'{folder}/mark.txt','r') as f:
            mark = f.read()


        mark_number = int(re.search(r'\d+', mark).group())
        if mark_number < 50:

            if data:   #this runs the marks is less then 50 and then it deletes all
                       #the task that is completed and pending and skiped for that 
                       #level so that user can do the task again
                       
                for lvl in data['levels']:    # so we also add all the complete,
                                              #pending and skip check as (show_task) have
                    all_done = all(
                        t['task_name'] in completes or
                        t['task_name'] in pending_names or  
                        t['task_name'] in skips       
                        for t in lvl['tasks']
                    )
                    if all_done and lvl['level_number'] not in question_levels:
                        for t in lvl['tasks']:
                            if t['task_name'] in completes:
                                completes.remove(t['task_name'])

                        with open(f'{folder}/complete.txt', 'w') as f:
                            json.dump(completes,f)

                        updated_pending = []
                        level_task_name = [t['task_name'] for t in lvl['tasks']]

                        for p in pending:
                            if p['task_name'] not in level_task_name:
                                updated_pending.append(p)
                        with open(f'{folder}/pending.json', 'w') as f:
                            json.dump(updated_pending, f)

            file_name = ['answered.txt','question.json','mark.txt']
            remove_file(file_name)

            return redirect(url_for('show_task'))
        
        else:
            answered.append(question)
            with open(f'{folder}/answered.txt', 'w') as f:
                json.dump(answered, f)
            return redirect(url_for('show_question'))
    try:
        with open(f'{folder}/question.json','r') as f:
            content = json.load(f)
    except:
        return redirect(url_for('home'))
    
    question = None          #so this is the main logic for showing the question page,
                             #it checks if any question is not answered then it shows that question
    for qust in list(content):
        if qust not in answered:
            question = qust
            break
    else:

        if data:                        #this is the logic for checking if all tasks are completed
                                        #for a level then it writes that level number in question.txt
            for lvl in data['levels']:
                all_done = all(t['task_name'] in completes or
                               t['task_name'] in pending_names or
                               t['task_name'] in skips
                               for t in lvl['tasks'])
                if all_done and lvl['level_number'] not in question_levels:
                    write_question_level(lvl['level_number'])
                    break
        
        files = ['mark.txt','answered.txt','question.json']
        remove_file(files)
        return redirect(url_for('show_task')) #if user failed the 50 mark then it goes to the
                                              #(show_task) page
        
    return render_template('question.html',
                               question = question)

        
@backend.route('/pending_task',methods=['GET','POST'])
def pending_task():
    folder = user_folder()
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
            try:
                with open(f'{folder}/xp.txt', 'r') as f:
                    x = int(f.read())
            except FileNotFoundError:
                x = 0
            n = x + a
            # print(f'complete: {n}')

            with open(f'{folder}/xp.txt','w') as f:
                f.write(str(n))

            with open(f'{folder}/pending.json','w') as f:
                json.dump(ddata,f)

            pending = pending_complete()
            pending.append(task_name)
            with open(f'{folder}/pending_complete.txt','w') as f:
                json.dump(pending,f)
            
            return redirect(url_for('pending_task'))
        
        elif 'no' == action:
            
            c = xp_reward
            with open(f'{folder}/xp.txt', 'r') as f:
                l = int(f.read())
            o = l - c

            with open(f'{folder}/xp.txt','w') as f:
                f.write(str(o))

            pending_skips = pending_skip()
            pending_skips.append(task_name)
            with open(f'{folder}/pending_skip.txt','w') as f:
                json.dump(pending_skips,f)

            return redirect(url_for('pending_task'))
        
        elif 'quit' == action:
            return redirect(url_for('home'))
        

    tasks = None
    ind = None

    for tk in ddata:
        if (tk["task_name"] not in p_s and
            tk["task_name"] not in p_c):
            # clean = ddata.pop(ind)
            tasks = tk
            break
    else:
        files = ['pending_complete.txt','pending_skip.txt','pending.json','xp.txt']
        remove_file(files)
        return render_template('final.html')
    

    try:
        with open(f'{folder}/xp.txt','r') as f:
            content = f.read()
    except FileNotFoundError:
        content = '0'
    return render_template('pending_task.html',
                           tasks = tasks, content = content)


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
