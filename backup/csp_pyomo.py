
# coding: utf-8

# In[7]:


from pyomo.environ import *


# In[50]:


def parse_inputs(path):
    models = []
    mission_types = {}
    pilots = {}
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
                pilot = line[1]
                compat_string = list(line[3])
                compat = [int(i) for i in compat_string]            
                pilots[pilot] = compat
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
                models.append(line)
#     print()
    print("Number of missions:", len(missions.keys()), "and number of mission types: ", len(list(mission_types.keys())))
    print("Number of pilots:", len(pilots.keys()))
    print("Number of unique models:", len(models), "and number of total models:", sum(nuas))
    return(models, pilots, missions, nuas, mission_types)

    
models, pilots, missions, nuas, mission_types = parse_inputs("sample2.txt")   


# In[51]:


pilots


# In[52]:


model = ConcreteModel()

# number of missions
model.missions = range(len(missions.keys()))

# number of pilots
model.pilots = range(len(pilots.keys()))

#number of unique models
model.unique_models = range(len(models))


# In[53]:


model.pm = Var(model.pilots, model.unique_models, within = Binary)
model.tm = Var(model.missions, model.unique_models, within = Binary)

# each uav model can be used for a maximum of 3 times as many as the number of pilots driving that model
# and each uav model must be used at least 1 time as many as the number of pilots driving that model
model.model_mission = ConstraintList()
for m in model.unique_models:
    model.model_mission.add(sum(model.pm[p,m] for p in model.pilots) <= sum(model.tm[t,m] for t in model.missions))
    

# add constraints

#each pilot drives only uav:
model.pilot_single_uav = ConstraintList()
for pilot in model.pilots:
    model.pilot_single_uav.add(sum(model.pm[pilot,m] for m in model.unique_models) == 1)


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
    
        
# one mission has only one UAV
model.one_uav_per_mission = ConstraintList()
for t in model.missions:
    model.one_uav_per_mission.add(sum(model.tm[t, m] for m in model.unique_models) == 1)


#mission model compatibility constaint
model.mission_model_compatibility = ConstraintList()
mission_keys = list(missions.keys())
for t in model.missions:
    compatible_models = missions[mission_keys[t]]
    for m in model.unique_models:
        compatibility = compatible_models[m]
        model.mission_model_compatibility.add(model.tm[t,m] <= compatibility)

model.objective = Objective(expr = sum(model.tm[t, 1] for t in model.missions), sense = maximize )
# In[55]:


# from pyomo.opt import SolverFactory


# # In[59]:


# opt2 = SolverFactory("glpk")


# # In[60]:


# results=opt2.solve(model, tee=True)

