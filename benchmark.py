import src.pydevlpr as pyd
import time

ALL_DATA = []
start = 0

def count(data):
    global ALL_DATA, start
    if len(ALL_DATA) == 0:
        start = time.time()
    ALL_DATA.append(data)

pyd.add_callback(pyd.DataTopic.RAW_DATA_TOPIC, 6, count)

end = 0
while True:
    if len(ALL_DATA) == 0:
        print("WAITING")
        #start = time.time()
    if len(ALL_DATA) > 15000:
        end = time.time()
        pyd.remove_callback(pyd.DataTopic.RAW_DATA_TOPIC, 6, count)
        break

print(f'RESULT:\n\tSTART: {start}, END: {end}, DELTA: {end - start}\n\tLEN(DATA): {len(ALL_DATA)}')
with open("output.txt", "w") as f:
    f.write("\n".join(ALL_DATA))
pyd.stop()
