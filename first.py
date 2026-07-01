from dotenv import load_dotenv
from openai import OpenAI
from apii import api_key
from ollama import chat
import json
import os

class moddle:
    pass
    def __init__(self,prompt):
        self.prompt = prompt

    def moddl(self):
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
             'content':f'{self.prompt}'}
             ],
            # temperature=0.2
            )
        content = response.choices[0].message.content
        print(content)
        data = json.loads(content)
        with open('level.json','w') as f:
            json.dump(data,f)

class functionality:
    def __init__(self):
        pass
    def dataa(self):
        with open('level.json','r') as f:
            data=json.load(f)

        return data

    def features(self):
        data = self.dataa()
        complete = self.complete()
        print(f'{complete}\n')

        for ind, task in enumerate(data['levels'], start=1):

            print('\n')
            print(f'Resource: {task['Learning_Resource']}')
            print(f'Level: {task['level_number']}')
            print(f'Level Name: {task['level_name']}')
            print(f'Description: {task['description']}')
            print(f'Total xp: {task['total_xp_required']}\n')
            print('Tasks Detail:\n')
            for ind, tasks in enumerate(task['tasks'], start=1):
                print(f'Task Index: {ind}')
                print(f'Task Name: {tasks['task_name']}')
                print(f'Difficulty Level: {tasks['difficulty']}')
                print(f'xp point: {tasks['xp_reward']}')
                print('\n')

                if tasks['task_name'] in complete:
                    print('Task already completed')
                else:
                    try:
                        while True:
                            r = input('Did you complete the task or u want to quit: ')
                            if r.lower() in ('quit','yes','no'):
                                break
                            print('Invalid responce\n')
                        if 'quit' == r.lower():
                            return
                        
                        elif 'yes' == r.lower():
                            point = tasks['xp_reward']
                            try:
                                with open('xp.txt','r') as f:
                                    dat = int(f.read())
                            except:
                                dat = 0
                            total = dat + point
                            print(total)
                            with open('xp.txt','w') as f:
                                f.write(str(total))
                            try:
                                with open('complete.txt','r') as f:
                                    # a = tasks['task_name']
                                    # f.write(f'{[a]}\n')
                                    content=f.read().strip()
                                    if content:
                                        a = json.loads(content)
                                    else:
                                        a = []
                            except FileNotFoundError:
                                a = []
                            a.append(tasks['task_name'])
                            with open('complete.txt','w') as f:
                                json.dump(a,f)
                                

                        elif 'no' == r.lower():
                            print('Task added to complete later.')
                            try:
                                with open('pending.json','r') as f:
                                    content=f.read().strip() # this will read the data in the file
                                    
                                    # print(f'content value:{content}')
                                    
                                    if content: # this will check if content is empty(none) then 'a' become (empty list) or not 
                                        #loads only parse (meaning it make file in python format)the file didint reaf the file 
                                        a = json.loads(content) # this will also read data in file but it help to append the list in the file
                                        # print(f'a value:{a}')
                                    else:
                                        a = []
                                    
                                    # a = json.load(content) if content else []
                                a.append({
                                'Task name': tasks['task_name'],
                                'Difficulty Level': tasks['difficulty'],
                                'xp point': tasks['xp_reward']})
                            
                                with open('pending.json','w') as f:
                                    json.dump(a,f)
                            except Exception as e:        
                                print(e)
                    except ValueError as e:
                        print(f'Try again {e}')
                                        
    def pending_task(self):
        try:
            with open('pending.json','r') as f:
                check = f.read().strip() #strip() removes whitespace from the beginning and the end of the string

                if check:
                    ddata = json.loads(check)
                    print('Pending Tasks.\n')
                    # print(ddata)
                    for ind, tasks in enumerate(list(ddata)): # (list(ddata)) get the copied list and it iterate through it even if list changes it doesnt affect the loop
                        print(f'Task Index: {ind}')
                        print(f'Task name: {tasks['Task name']}')
                        print(f'Difficulty Level: {tasks['Difficulty Level']}')
                        print(f'xp point: {tasks['xp point']}')
                        print('\n')
                    #print(tasks)
                        while True:
                            s = input('Did you complete the task: ')
                            if s in ('yes','no','quit'):
                                break
                            print('Invalid Input')

                        if 'yes' == s.lower():
                            a = tasks['xp point']
                            print(a)
                            clean = ddata.pop(ind)
                            with open('xp.txt', 'r') as f:
                                x = int(f.read())
                            
                            n = x + a
                            print(f'complete: {n}')
                            with open('xp.txt','w') as f:
                                f.write(str(n))

                            with open('pending.json','w') as f:
                                json.dump(ddata,f)

                            
                        elif 'no' == s.lower():
                            c = tasks['xp point']
                            with open('xp.txt', 'r') as f:
                                l = int(f.read())
                                
                            o = l - c
                            print(f'incomplete: {o}')
                            with open('xp.txt','w') as f:
                                f.write(str(o))

                            
                        elif 'quit' == s.lower():
                            return
                        
                        else:
                            print('file empty')
                            return
                        
        except FileNotFoundError as e:
            print(e)

    def complete(self):
        try:
            with open('complete.txt','r') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
                else:
                    return []
        except FileNotFoundError:
            return []



prommpt = input('>>')
modd = moddle(prommpt)
# b = modd.moddl()

fetur = functionality()
c = fetur.complete()
a = fetur.features()
b = fetur.pending_task()