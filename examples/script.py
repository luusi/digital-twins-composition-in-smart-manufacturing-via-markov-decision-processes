import itertools

services = {
    'a': {
        ('airoff', 'hotairon'): 'airhot', 
        ('airoff', 'coldairon'): 'aircold',
        ('airhot', 'hotairon'): 'airhot',
        ('airhot', 'airoff'): 'airoff',
        ('aircold', 'coldairon'): 'aircold',
        ('aircold', 'airoff'): 'airoff'
    },
    'b': {
        ('empty', 'fillbathtub'): 'filled',
        ('filled', 'emptybathtub'): 'empty'
    },
    'c': {
        ('unique', 'open'): 'unique',
        ('unique', 'close'): 'unique'
    },
    'd': {
        ('unique', 'ventkitchen'): 'unique'
    },
    'e': {
        ('s0', 'movetobedroom'): 's0',
        ('s2', 'movetobedroom'): 's0',
        ('s0', 'movetobathroom'): 's1',
        ('s1', 'movetobathroom'): 's1',
        ('s1', 'wash'): 's2',
        ('s3', 'movetokitchen'): 's3',
        ('s0', 'movetokitchen'): 's3',
        ('s3', 'cookeggs'): 's0',
        ('s3', 'preparetea'): 's0'}
}

target = {
    ('t0', 'hotairon'): 't1',
    ('t0', 'opendoorkitchen'): 't7',
    ('t0', 'movetokitchen'): 't8',
    ('t1', 'hotairon'): 't1',
    ('t1', 'fillupbathtub'): 't2',
    ('t2', 'opendoorbathroom'): 't2',
    ('t2', 'movetobathroom'): 't3',
    ('t3', 'movetobathroom'): 't3',
    ('t3', 'wash'): 't4',
    ('t4', 'movetobedroom'): 't5',
    ('t5', 'movetobedroom'): 't5',
    ('t5', 'emptybathtub'): 't6',
    ('t6', 'airoff'): 't7',
    ('t7', 'opendoorkitchen'): 't7',
    ('t7', 'movetokitchen'): 't8',
    ('t8', 'preparetea'): 't0',
    ('t8', 'cookeggs'): 't9',
    ('t8', 'movetokitchen'): 't8',
    ('t9', 'ventkitchen'): 't9'
}

prob = {('t0', 'hotairon'): 0.6,
        ('t0', 'opendoorkitchen'): 0.2,
        ('t0', 'movetokitchen'): 0.2,
        ('t1', 'hotairon'): 0.3,
        ('t1', 'fillupbathtub'): 0.7,
        ('t2', 'opendoorbathroom'): 0.5,
        ('t2', 'movetobathroom'): 0.5,
        ('t3', 'movetobathroom'): 0.2,
        ('t3', 'wash'): 0.8,
        ('t4', 'movetobedroom'): 1.0,
        ('t5', 'movetobedroom'): 0.1,
        ('t5', 'emptybathtub'): 0.9,
        ('t6', 'airoff'): 1.0,
        ('t7', 'opendoorkitchen'): 0.5,
        ('t7', 'movetokitchen'): 0.5,
        ('t8', 'preparetea'): 0.2,
        ('t8', 'movetokitchen'): 0.2,
        ('t8', 'cookeggs'): 0.6,
        ('t9', 'ventkitchen'): 1.0
        }

rewa = {('t0', 'hotairon'): 5,
        ('t0', 'opendoorkitchen'): 2,
        ('t0', 'movetokitchen'): 3,
        ('t1', 'hotairon'): 2,
        ('t1', 'fillupbathtub'): 4,
        ('t2', 'opendoorbathroom'): 2,
        ('t2', 'movetobathroom'): 3,
        ('t3', 'movetobathroom'): 4,
        ('t3', 'wash'): 8,
        ('t4', 'movetobedroom'): 10,
        ('t5', 'movetobedroom'): 3,
        ('t5', 'emptybathtub'): 7,
        ('t6', 'airoff'): 10,
        ('t7', 'opendoorkitchen'): 4,
        ('t7', 'movetokitchen'): 5,
        ('t8', 'preparetea'): 2,
        ('t8', 'movetokitchen'): 3,
        ('t8', 'cookeggs'): 7,
        ('t9', 'ventkitchen'): 10
        }


def Am(services):
    srv = set()
    for element in services:
        srv.add(-1)
        srv.add(element)
    return (srv)


print(Am(services))


def Sigmaz(services):
    dictz = dict()
    i = 0
    for key in services:
        for (state, action) in services[key]:
            dictz[i] = dictz.get(i, set()) | {key + '_' + state}
        i += 1
    # return(dictz)

    someset = [
        dictz[0],
        dictz[1],
        dictz[2],
        dictz[3],
        dictz[4]

    ]
    result = list(itertools.product(*someset))
    return (result)


print(Sigmaz(services))


def Sigmat(target):
    targ = set()
    for key in target:
        targ.add(key[0])
    return (targ)


print(Sigmat(target))


def A(target):
    action = set()
    for key in target:
        action.add(key[1])
    return (action)


print(A(target))


def ai(services):
    acti = set()
    for key in services:
        for s, a in services[key]:
            acti.add((a, key))

    return (acti)


print(ai(services))


def Sm(services, target):
    someset = [
        Sigmaz(services),
        Sigmat(target),
        A(target)
    ]
    result = list(itertools.product(*someset))
    # return(result)
    dictSm = dict()
    i = 0
    for s in result:
        dictSm[i] = s
        i += 1
    # return(dictionarySm)
    srv = Am(services)
    serv = set()
    for j in srv:
        if j == -1:
            continue
        else:
            serv.add(j)
    # return(serv)

    someset2 = [
        Sigmaz(services),
        Sigmat(target),
        A(target)
    ]
    res1 = list(itertools.product(*someset2))
    res2 = res1 + [-2, -1]
    # return(res2)

    out = set()
    # counter=0
    for ele in res2:
        if (ele == -2 or ele == -1):
            continue
        else:
            actio = ele[2]  # azioni
            # return(acti)
            statoInizial = ele[0][0]
            # return(statoIniziale)
            statoInizialeTarg = ele[1]
            # return(statoInizialeTarget)

            for key, value in services.items():
                for s, a in value.items():
                    if (actio == s[1] and statoInizial[2:] == s[0]):
                        for k in target:
                            if (actio == k[1] and statoInizialeTarg == k[0]):
                                for ke, va in prob.items():
                                    if (ke == (statoInizialeTarg, actio)):
                                        # counter+=1
                                        out.add(va)

    # return(counter)
    # return(out)
    someset1 = [
        dictSm.keys(),
        serv,
        dictSm.keys()
    ]
    res = list(itertools.product(*someset1))
    # return(res)
    somese = [
        dictSm.keys(),
        dictSm.keys()
    ]
    resi = list(itertools.product(*somese))
    # return(resi)
    unique_list = []
    counter = 0
    for u in resi:
        u1 = u[0]
        u2 = u[1]
        if (u1 != u2):
            counter += 1
            unique_list.append((u1, u2))

    return (counter)
    # return(unique_list)

    srv1 = Am(services)
    serv1 = set()
    for h in srv1:
        if h != -1:
            continue
        else:
            serv1.add(h)

    # counter=0
    out1 = set()
    for element in res:
        service = element[1]  # servizi a,b
        act = dictSm[element[0]][2]  # azioni
        sigmat1 = dictSm[element[2]][1]
        act1 = dictSm[element[2]][2]
        initialState = dictSm[element[0]][0][ord(service) - ord('a')]
        # return(statoIniziale)
        finalState = dictSm[element[2]][0][ord(service) - ord('a')]
        # return(statoFinale)
        initialStateT = dictSm[element[0]][1]
        finalStateT = dictSm[element[2]][1]
        for key, value in services.items():
            for s, a in value.items():
                if (service == key and act == s[1] and initialState[2:] == s[0] and finalState[2:] == a):
                    for k in target:
                        if (act == k[1] and initialStateT == k[0] and finalStateT == target[k]):
                            for ke, va in prob.items():
                                if (ke == (finalStateT, act1)):
                                    # counter+=1
                                    out1.add(va)


# return(counter)
# return(out1)


print(Sm(services, target))


def reward(services, target):
    someset = [
        Sigmaz(services),
        Sigmat(target),
        A(target)
    ]
    result = list(itertools.product(*someset))
    # return(result)
    dictSm = dict()
    i = 0
    for r in result:
        dictSm[i] = r
        i += 1
    # return(dictSm)

    someset = [
        dictSm.keys(),
        Am(services),
    ]
    res = list(itertools.product(*someset))
    # return(res)

    acti = (ai(services))
    # return(acti)
    out = set()
    for element in res:
        act = dictSm[element[0]][2]  # azione
        state = dictSm[element[0]][1]  # t0..
        sigmaz = dictSm[element[0]][0]
        service = element[1]
        for el in acti:
            if (act in el and service in el):
                for k, v in rewa.items():
                    if ((state, act) == k):
                        out.add(v)
    return (out)


print(reward(services, target))
