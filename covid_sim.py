import scipy as sp
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import io
import requests

### actual data source from nytimes
url="https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv"
s=requests.get(url).content
act_dat=pd.read_csv(io.StringIO(s.decode('utf-8')))
### example filter on NYC
z= act_dat[act_dat['county']=='New York City']

class person():
    def __init__(self,age,network_size):
        self.age = age
        self.network_size = network_size
        self.sick = False
        self.dead = False
        self.immune = False
        self.severity = 0
        self.clock = 0
# Population distributions source : https://www.statista.com/statistics/270000/age-distribution-in-the-united-states/
it_pop_buckets=[.13,.64,.23]
us_pop_buckets=[.19,.65,.16]
#mean daily contacts = 10
#https://www.researchgate.net/figure/Distribution-of-a-the-total-number-of-contacts-during-the-study-period-b-the-average_fig1_318716964

def infection_prob(person,infection_rate):
    if (person.immune) | (person.dead) | (person.sick):
        return person
    else:
        infection_prob = infection_rate*person.network_size
        if np.random.rand()<infection_prob:
            person.sick=True
            person.severity = max([0,np.random.normal(np.log(person.age),1)])
        return person


def outcome_prob(person,mortality_discount):
    if (person.sick)&(person.clock>=10)&(person.clock<=28)&(person.immune==False):
        dead_prob=person.severity * mortality_discount
        if np.random.rand()<dead_prob:
            person.dead = True
            return person 
    elif (person.clock>28) & (person.dead==False): 
        person.immune=True
        return person
    return person

def create_person(distribution,mean_contacts):
    val=np.random.rand()
    contacts=max(1,np.random.normal(mean_contacts,5))
    if val<=distribution[0]:
        age = np.random.randint(1,15)
        p=person(age,contacts)
    elif (val>distribution[0])&(val<=distribution[1]):
        age = np.random.randint(15,65)
        p=person(age,contacts)
    else:
        age = np.random.randint(65,99)
        p=person(age,contacts)
    return p

def create_pop(size,demographic,contact=10):
    people = []
    #size = 1000
    for i in range(size):
        people.append(create_person(demographic,contact))
    return people


def simulate(pop,scale,demo,contact,time,init_infections,mort_discount):
    dead,infect,rec,hospital=[],[],[],[]
    people = create_pop(pop,demo,contact[0])
    for i in range(init_infections):
        people[i].sick = True
    for t in range(time[0]):
        deaths = sum([i.dead for i in people])
        infections=sum([i.sick for i in people])
        recoveries=sum([i.immune for i in people])
        i_rate = float(infections)/len(people)/scale
        for person in people:
            if (contact[1]>-1) and (t==time[1]):
                person.network_size=contact[1]
            if person.sick:
                person.clock+=1
            person = infection_prob(person,i_rate)
            person = outcome_prob(person,mort_discount)
        hosp = len([i for i in people if (i.severity>=4)&(i.immune==False)])
        print('Time: ',t,' Deaths: ',deaths, ' Recoveries: ',recoveries, 'Infections: ',infections,'hospital: ', hosp)
        dead.append(deaths),infect.append(infect),rec.append(recoveries),hospital.append(hosp)
    return people,dead,infect,rec,hospital


### Example levels of distancing (given NYC at 30 contacts)
dist,name=[-1,15,10,5,2],['None','50% Dist','66% Dist','85% Dist','95% Dist']

for i in range(len(dist)):
    plt.plot(range(1,60),[dead[dist[i]][j]-dead[dist[i]][j-1] for j in range(1,60)],label=name[i])
plt.plot(range(1,z.shape[0]),[z['deaths'].values[j]-z['deaths'].values[j-1] for j in range(1,z.shape[0])],
         color='black',label='NYC True')
plt.legend()