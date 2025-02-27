import plotly.express as px 
import pandas as pd 

import plotly.express as px
from plotly.offline import plot
from plotly.subplots import make_subplots

# Assemble plots
def plot_objectives(violations = None, costs = None):
    # Do nothing if not told to do anything
    if(violations == None and costs == None):
        return
    
    # Plot otherwise
    figures = []
    if(violations != None):
        figures.append(create_plot(violations,name = "Violations"))
    if(costs != None):
        figures.append(create_plot(costs,name = "Costs"))

    # Show figures
    for fig in figures:
        fig.show()


# Create a single plot from data
def create_plot(data_dict,name = "Costs"):
    iterations = [i+1 for i in range(len(data_dict[list(data_dict.keys())[0]]))]
    data_dict["Iteration"] = iterations
    fig = px.line(data_dict, x="Iteration", y=list(data_dict.keys())[:-1], title=name)
    fig.update_layout(legend=dict(title=name), 
                      xaxis=dict(tickformat=",d"),
                      yaxis=dict(title="Value"))
    return fig


if __name__ == "__main__":
    # Example data
    example_violations_dict = {"RoomGenderMix": [1,2,3,4,5],
                               "PatientRoomCompatibility": [2,3,4,5,6],
                               "SurgeonOvertime": [3,4,5,6,7],
                               "OperatingTheaterOvertime": [4,5,6,7,8],
                               "MandatoryUnscheduledPatients": [5,6,7,8,9],
                               "AdmissionDay": [6,7,8,9,10],
                               "RoomCapacity": [7,8,9,10,11],
                               "NursePresence": [8,9,10,11,12],
                               "UncoveredRoom": [9,10,11,12,13]}
    
    example_costs_dict = {"RoomAgeMix": [1,2,3,4,5],
                          "RoomSkillLevel": [2,3,4,5,6],
                          "ContinuityOfCare": [3,4,5,6,7],
                          "ExcessiveNurseWorkload": [4,5,6,7,8],
                          "OpenOperatingTheater": [5,6,7,8,9],
                          "SurgeonTransfer": [6,7,8,9,10],
                          "PatientDelay": [7,8,9,10,11],
                          "ElectiveUnscheduledPatients": [8,9,10,11,12]}
    
    # Example single plots
    plot_objectives(violations = example_violations_dict)
    plot_objectives(costs = example_costs_dict)

    # Example dual plot (loads both plots)
    plot_objectives(violations = example_violations_dict,
                    costs = example_costs_dict)

def solution_summary(data, solution):
    summary={"room_status":[],"surgeon_status":[],"theater_status":[]}

    print('')
    print('Rooms: remaining capacity per day')
    for r in data.data["rooms"]:
        out = r['id'] + ' (capacity ' + str(r['capacity']) + '): |'
        for d in data.all_days:
            used = len(solution["room_allocation"][str((d,r["id"]))])
            avail = r['capacity']-used
            out = out + str(avail) + ','
        out = out + '|'
        print(out)
        summary['room_status'].append(out)

    print('')
    print('Surgeons: remaining time (mins) per day')
    for s in data.data['surgeons']:
        out = s['id'] + ': |'
        for d in data.all_days:
            out = out + str(solution['surgeon_allocation'][str((d,s['id']))]) + ','
        out = out + '|'
        print(out)
        summary['surgeon_status'].append(out)

    print('')
    print('Theaters: remaining time (mins) per day')    
    for t in data.data['operating_theaters']:
        out = t['id'] + ': |'
        for d in data.all_days:
            out = out + str(solution['theater_allocation'][str((d,t['id']))]) + ','
        out = out + '|'
        print(out)
        summary['theater_status'].append(out)
    print('')
        
    return summary
