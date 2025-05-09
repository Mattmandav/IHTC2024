import os
import plotly.express as px 
import pandas as pd
from src.utils.plotter import create_plot

penalties_folder = "data/individual_costs"

# Collect all of the costs
files = sorted([
        f for f in os.listdir(penalties_folder)
        if os.path.isfile(os.path.join(penalties_folder, f))
        ])

# List of all instances
instances = ["i01","i02","i03","i04","i05","i06","i07","i08","i09","i10",
            "i11","i12","i13","i14","i15","i16","i17","i18","i19","i20",
            "i21","i22","i23","i24","i25","i26","i27","i28","i29","i30"]

# Initial dictionary
scores_dict = {"Instance": ["i01","i02","i03","i04","i05","i06","i07","i08","i09","i10",
                            "i11","i12","i13","i14","i15","i16","i17","i18","i19","i20",
                            "i21","i22","i23","i24","i25","i26","i27","i28","i29","i30"]*2,
               "Selection": ["Best"]*30 + ["Our Best"]*30,
               "Acceptance": ["Best"]*30 + ["Our Best"]*30,
               "Total": [3842,1264,10490,1884,12760,10671,5026,6291,6682,20820,
                         25938,12430,17328,9746,12486,10139,40535,37660,44587,29098,
                         24703,47861,37550,33221,11517,64613,51828,75172,12475,37943,
                         5217,2566,11535,4269,17839,11659,13230,14596,14455,32955,
                         32479,18887,28879,19208,31820,21510,108385,54259,76216,44924,
                         55600,99055,64186,46039,22901,137080,160605,93283,31205,62724,
                         ],  
               "RoomAgeMix": [0]*60,
               "RoomSkillLevel": [0]*60,
               "ContinuityOfCare": [0]*60,
               "ExcessiveNurseWorkload": [0]*60,
               "OpenOperatingTheater": [0]*60,
               "SurgeonTransfer": [0]*60,
               "PatientDelay": [0]*60,
               "ElectiveUnscheduledPatients": [0]*60,}

costs = [k for k in scores_dict if k not in ["Instance","Selection","Acceptance","Total"]]

# Filling dictionary
for f in files:
    # Get features
    instance_name = f[:3]
    # Selection
    if("mcrl" in f):
        selection_method = "MCRL"
    elif("qlearner" in f):
        selection_method = "Q-Learner"
    elif("random" in f):
        selection_method = "Random"
    else:
        selection_method = "None"
    # Acceptance
    if("sa" in f):
        acceptance_method = "Simulated Annealing"
    elif("r2r" in f):
        acceptance_method = "Record-to-record"
    elif("improve_only" in f):
        acceptance_method = "Improving Only"
    else:
        acceptance_method = "None"
    # Get data
    with open(os.path.join(penalties_folder, f), 'r') as file:
        file_data = pd.read_csv(file)
    # Populate table
    scores_dict["Instance"].append(instance_name)
    scores_dict["Selection"].append(selection_method)
    scores_dict["Acceptance"].append(acceptance_method)
    total = 0
    for c in costs:
        value = list(file_data[c])[-1]
        total += value
        scores_dict[c].append(value)
    scores_dict["Total"].append(total)

scores_dataframe = pd.DataFrame(scores_dict)

configurations = {
    ("Our Best","Our Best"): "Our Best",
    ("Best","Best"): "Best",
    ("None","None"): "Initial Solution",
    ("Random","Improving Only"): "Random with IO",
    ("Random","Simulated Annealing"): "Random with SA",
    ("Random","Record-to-record"): "Random with R2R",
    ("MCRL","Simulated Annealing"): "MCRL with SA",
    ("Q-Learner","Simulated Annealing"): "Q-learning with SA",
}

# Creating long data with averages
scores_dataframe_average = pd.DataFrame(columns=["Configuration","Penalty Type","Average Value"])
scores_dataframe_instance = pd.DataFrame(columns=["Configuration","Instance","Total Penalty"])
for config in configurations:
    # Getting the data for that configuration
    config_data = scores_dataframe.loc[
        (scores_dataframe["Selection"] == config[0]) &
        (scores_dataframe["Acceptance"] == config[1])
        ]
    # Updating the average table
    scores_dataframe_average.loc[len(scores_dataframe_average)] = [
        configurations[config], "Total", sum(config_data["Total"])/len(config_data["Total"])
    ]
    for c in costs:
        scores_dataframe_average.loc[len(scores_dataframe_average)] = [
            configurations[config], c, sum(config_data[c])/len(config_data[c])
        ]
    # Updating the instance table
    for index, row in config_data.iterrows():
        scores_dataframe_instance.loc[len(scores_dataframe_instance)] = [
            configurations[config], row["Instance"], row["Total"]
        ]


# Plotting for powerpoint
# First plot
data1 = scores_dataframe_average.loc[scores_dataframe_average["Configuration"].isin(["Initial Solution"])]
fig = px.histogram(
    data1,
    x = "Penalty Type",
    y = "Average Value",
    color = "Configuration",
    barmode = "group",
)
fig.update_layout(yaxis_title="Average Value")
fig.update_layout(title="Average penalty value against penalty type")
fig.update_layout(showlegend=False)
fig.write_image("data/plots/fig1.svg", width=1200, height=534, scale=2.0)
fig.show()

# Second plot
data1 = scores_dataframe_average.loc[scores_dataframe_average["Configuration"].isin([
    "Initial Solution",
    "Random with IO",
    ])]
fig = px.histogram(
    data1,
    x = "Penalty Type",
    y = "Average Value",
    color = "Configuration",
    barmode = "group",
)
fig.update_layout(yaxis_title="Average Value")
fig.update_layout(title="Average penalty value against penalty type")
fig.write_image("data/plots/fig2.svg", width=1200, height=534, scale=2.0)
fig.show()

# Third plot (Trace plot of solution value for i27)
with open(os.path.join(penalties_folder, "i27_random_improve_only.csv"), 'r') as file:
    i27_file_data = pd.read_csv(file)
i27_dict = i27_file_data.to_dict("list")
fig = create_plot(i27_dict)
fig.update_traces(line=dict(width=5))
fig.update_layout(yaxis_title="Penalty Value")
fig.update_layout(title="Penalty value against iteration for instance i27")
fig.write_image("data/plots/fig3.svg", width=1200, height=534, scale=2.0)
fig.show()

# Fourth plot
data1 = scores_dataframe_average.loc[scores_dataframe_average["Configuration"].isin([
    "Initial Solution",
    "Random with IO",
    "Random with SA",
    "Random with R2R",
    ])]
fig = px.histogram(
    data1,
    x = "Penalty Type",
    y = "Average Value",
    color = "Configuration",
    barmode = "group",
)
fig.update_layout(yaxis_title="Average Value")
fig.update_layout(title="Average penalty value against penalty type")
fig.write_image("data/plots/fig4.svg", width=1200, height=534, scale=2.0)
fig.show()

# Fifth plot
data1 = scores_dataframe_average.loc[scores_dataframe_average["Configuration"].isin([
    "Random with SA",
    "MCRL with SA",
    "Q-learning with SA",
    ])]
fig = px.histogram(
    data1,
    x = "Penalty Type",
    y = "Average Value",
    color = "Configuration",
    barmode = "group",
)
fig.update_layout(yaxis_title="Average Value")
fig.update_layout(title="Average penalty value against penalty type")
fig.write_image("data/plots/fig5.svg", width=1200, height=534, scale=2.0)
fig.show()

# Sixth plot
data1 = scores_dataframe_instance.loc[scores_dataframe_instance["Configuration"].isin([
    "Best",
    "Our Best",
    ])]
fig = px.histogram(
    data1,
    x = "Instance",
    y = "Total Penalty",
    color = "Configuration",
    barmode = "group",
)
fig.update_layout(yaxis_title="Total Penalty")
fig.update_layout(title="Total penalty value against instance")
fig.write_image("data/plots/fig6.svg", width=1200, height=534, scale=2.0)
fig.show()

# Final plot
final_scores = {"Team": ["t01","t02","t03","t04","t05","t06","t07","t08","t09","t10",
                         "t11","t12","t13","t14","t15","t16","t17","t18","t19","t20",
                         "t21","t22","t23","t24","t25","t26","t27","t28","t29","t30",
                         "t31", "Us"],
               "Average Penalty": [
                   26627.96667, 25123.43333, 6698051.533, 13362494.13, 25382.36667, 24372.06667,	27748.9,	50014369.97,	26070.16667,	25092.43333,
                   26274.76667,	27551.5,	25038.26667,	27252.06667,	16698767.3,	44729.5,	36870.13333,	30080.63333,	23358086.13,	30920.9,
                   36224.96667,	25264.7,	42557.2,	25442.83333,	41963.26667,	23355296.1,	30856.06667,	28580.33333,	13361937.87,	24981.9,
                   26996.8,	44585.53333,
                   ],
               "Type": [0,0,1,1,0,0,0,1,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,1,0,0,1,0,0,2]
}
final_dataframe = pd.DataFrame(final_scores)
fig = px.histogram(
    final_dataframe,
    x = "Team",
    y = "Average Penalty",
    color = "Type",
)
fig.update_layout(yaxis_title="Average Value")
fig.update_layout(title="Average penalty value against team")
fig.update_layout(showlegend=False)
fig.update_layout(yaxis_range=[0,70000])
fig.update_xaxes(categoryorder='array', categoryarray= final_dataframe["Team"])
fig.write_image("data/plots/fig7.svg", width=1200, height=534, scale=2.0)
fig.show()

