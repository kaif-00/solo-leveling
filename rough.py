# d = {'task_name': 'Master Stance', 'difficulty': 'easy', 'xp_reward': 10}

# print(d['task_name'])

# d = {"Task name": "Master Stance", "Difficulty Level": "easy", "xp point": 10}

# for i,j in enumerate(d.items()):
#     print(f'{j[0]}: {j[1]}')

a = [{"Task name": "Complete MIT Robotics Course Lesson 1", "Difficulty Level": "easy", "xp point": 10}, {"Task name": "Assemble a Simple Robot Arm", "Difficulty Level": "medium", "xp point": 20}]

for i in range(len(a)):
    print(a[i])
a.pop(0)
print(a)