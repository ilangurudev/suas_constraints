# coding: utf-8


from pyomo.environ import *
from pyomo.opt import SolverFactory
import sys

input_filename = sys.argv[1]
output_filename = sys.argv[2]



def parse_inputs(path):
    models = []
    mission_types = {}
    pilots = {}
    pilots_favorable = []
    missions = {}
    nuas = []
    f = open(path, encoding="utf8", errors='ignore')
    inputs = f.readlines()
    f.close()
    for i in range(len(inputs)):
        line = inputs[i]
        if not line[0] == "%":
            line = line.rstrip()
            if line[0:3] == "MT ":
                line = line.replace("  "," ")
                line = line.split(" ")  
                mission_type = line[1]
                compat_string = list(line[2])
                compat = [int(i) for i in compat_string]            
                mission_types[mission_type] = compat
            elif line[0:2] == "P ":
                line = line.replace("  "," ")
                line = line.split(" ")
#                 print(line, line[3])
                pilot = line[1]
                compat_string = list(line[2])
                compat = [int(i) for i in compat_string] 
                pilots[pilot] = compat
                fav_string = list(line[3])
                fav = [int(i) for i in fav_string]            
                pilots_favorable.append(fav)
            elif line[0:2] == "M ":
                line = line.replace("  "," ")
                line = line.replace("M ", "")
                line = line.replace("M", "")
                line = line.split(" ")
                mission_num = line[0]
                mission_type = line[1][0]
                compat = mission_types[mission_type]
                missions[mission_num] = compat
            elif "NUAS" in line:
                line = line.replace("  "," ")
                line = line.split(" ")
                l_nuas = list(line[1])
                l_nuas = [int(i) for i in l_nuas]
                for i in l_nuas:
                    nuas.append(i)
            else:   
                # print(line)
                models.append(line)
#     print()
    print("Number of missions:", len(missions.keys()), "and number of mission types: ", len(list(mission_types.keys())))
    print("Number of pilots:", len(pilots.keys()))
    print("Number of unique models:", len(models), "and number of total models:", sum(nuas))
    return(models, pilots, pilots_favorable ,missions, nuas, mission_types)

    
models, pilots, pilots_favorable, missions, nuas, mission_types = parse_inputs(input_filename)   


# print(models)
# print(pilots)
# print(missions)
# print(nuas)
# print(mission_types)
# print(pilots_favorable)


#Modelling Starts

model = ConcreteModel()

# number of missions
model.missions = range(len(missions.keys()))

# number of pilots
model.pilots = range(len(pilots.keys()))

#number of unique models
model.unique_models = range(len(models))


model.pm = Var(model.pilots, model.unique_models, within = Binary)
model.tm = Var(model.missions, model.unique_models, within = Binary)


# add constraints

# each uav model can be used in a maximum of 3 times as many missions as the number of pilots driving that model
# and each uav model must be used in at least 1 time as many missions as the number of pilots driving that model


model.model_mission = ConstraintList()
for m in model.unique_models:
    model.model_mission.add(sum(model.tm[t,m] for t in model.missions) <= 3*sum(model.pm[p,m] for p in model.pilots))
    model.model_mission.add(sum(model.tm[t,m] for t in model.missions) >= sum(model.pm[p,m] for p in model.pilots))
#     model.model_mission.add(3*sum(model.tm[p,m] for p in model.pilots) >= sum(model.tm[t,m] for t in model.missions))
#     model.model_mission.add(sum(model.tm[p,m] for p in model.pilots) <= sum(model.tm[t,m] for t in model.missions))
        


#each pilot drives maximum 1 uav:
model.pilot_single_uav = ConstraintList()
for pilot in model.pilots:
    model.pilot_single_uav.add(sum(model.pm[pilot,m] for m in model.unique_models) <= 1)


#pilot model compatibility constraint
model.pilot_model_compatibility = ConstraintList()
pilot_keys = list(pilots.keys())
for pilot in model.pilots:
    compatible_models = pilots[pilot_keys[pilot]]
    for m in model.unique_models:
        compatibility = compatible_models[m]
        model.pilot_model_compatibility.add(model.pm[pilot, m] <= compatibility)
        
    
#Number of models constraint?
model.num_models_constraint = ConstraintList()
for m in model.unique_models:
    num_available = nuas[m]
    model.num_models_constraint.add(sum(model.pm[p, m] for p in model.pilots) <= num_available)
    
        
# one mission has at the maximum one UAV 
#(preferably atleast 1 uav but that might cause infeasibility, so incorporated into objective)
model.one_uav_per_mission = ConstraintList()
for t in model.missions:
    model.one_uav_per_mission.add(sum(model.tm[t, m] for m in model.unique_models) <= 1)


#mission model compatibility constaint
model.mission_model_compatibility = ConstraintList()
mission_keys = list(missions.keys())
for t in model.missions:
    compatible_models = missions[mission_keys[t]]
    for m in model.unique_models:
        compatibility = compatible_models[m]
        model.mission_model_compatibility.add(model.tm[t,m] <= compatibility)
        
# model.objective = Objective(expr = summation(model.tm) +  , 
#                             sense = maximize )

model.objective = Objective(expr = 60*summation(model.tm) + sum(pilots_favorable[p][m]*model.pm[p, m] for p in model.pilots for m in model.unique_models),
                            sense = maximize )


opt2 = SolverFactory("glpk")
results=opt2.solve(model)

mission_keys = list(missions.keys())
pilot_keys = list(pilots.keys())

def xstr(s):
    if s is None:
        return 'None'
    return str(s)

f = open(output_filename, 'w')
for t in model.missions:
    current_model = None
    current_pilot = None
    fav = None
    for m in model.unique_models:
        if model.tm[t , m].value == 1:
            current_model = models[m]
            for p in model.pilots:
                if model.pm[p , m].value > 0 and model.pm[p , m].value <= 3:
                    model.pm[p , m].value = model.pm[p , m].value + 1.0        
                    current_pilot = pilot_keys[p]
                    fav = "True" if pilots_favorable[p][m] > 0 and model.pm[p,m].value > 0 else "False"
                    break
    mission_model_pilot = "M" + mission_keys[t] + " " + xstr(current_model) + " " + xstr(current_pilot) + " " + xstr(fav) + '\n'
    print(mission_model_pilot)
    f.write(mission_model_pilot)

f.close() 
