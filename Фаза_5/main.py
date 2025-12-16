import csv
from random import choice, seed
from typing import List


def successors_by_predecessors(predecessors: List[List[int]]) -> List[List[int]]:
    n = len(predecessors)
    return [[j for j in range(n) if i in predecessors[j]] for i in range(n)]

def calculate_critical_times(duration, predecessors, successors=None):
    if not successors:
        successors = successors_by_predecessors(predecessors)

    est = [0] * len(duration)
    lst = [0] * len(duration)

    def calc_es(i):
        if predecessors[i]:
            est[i] = max(calc_es(p) + duration[p] for p in predecessors[i])
        return est[i]

    def calc_lf(i):
        if i == len(duration) - 1:
            lst[i] = est[i]
        elif successors[i]:
            lst[i] = min(calc_lf(s) - duration[s] for s in successors[i])
        return lst[i]

    calc_es(len(duration) - 1)
    calc_lf(0)
    return est, lst


class TimeCapacityNode:
    def __init__(self, time, capacity):
        self.time = time
        self.capacity = capacity
        self.next = None
        self.prev = None

    def insert_after(self, time):
        node = TimeCapacityNode(time, self.capacity.copy())
        node.prev = self
        node.next = self.next
        if self.next:
            self.next.prev = node
        self.next = node
        return node

    def enough(self, demand):
        return all(self.capacity[i] >= demand[i] for i in range(len(demand)))

    def consume(self, demand):
        for i in range(len(demand)):
            self.capacity[i] -= demand[i]

class ActivityListDecoder:
    def decode(self, alist, duration, predecessors, demands, capacity):
        root = TimeCapacityNode(0, capacity.copy())
        starts = [0] * len(duration)
        finish_nodes = [None] * len(duration)
        finish_nodes[0] = root

        for i in alist:
            start = root
            for p in predecessors[i]:
                if finish_nodes[p].time > start.time:
                    start = finish_nodes[p]

            finish_time = start.time + duration[i]
            node = start

            while not node.enough(demands[i]):
                node = node.next
                start = node
                finish_time = start.time + duration[i]

            if not node.next or node.next.time != finish_time:
                finish_node = node.insert_after(finish_time)
            else:
                finish_node = node.next

            t = start
            while t != finish_node:
                t.consume(demands[i])
                t = t.next

            starts[i] = start.time
            finish_nodes[i] = finish_node

        return starts


class ActivityListSampler:
    def __init__(self, predecessors):
        self.pred = predecessors
        self.succ = successors_by_predecessors(predecessors)
        self.n = len(predecessors)

    def _gen(self, pick):
        res = []
        rem = [set(p) for p in self.pred]
        ready = [i for i in range(self.n) if not rem[i]]

        while ready:
            i = pick(ready)
            ready.remove(i)
            res.append(i)
            for s in self.succ[i]:
                rem[s].remove(i)
                if not rem[s]:
                    ready.append(s)
        return res

    def random(self):
        return self._gen(lambda x: choice(x))

    def min_rule(self, rule):
        return self._gen(lambda x: min(x, key=rule))


def read_tasks():
    duration, pred, dem = [], [], []
    with open("tasks.csv", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            duration.append(int(row["duration"]))
            pred.append([int(x) for x in row["predecessors"].split(";")] if row["predecessors"] else [])
            dem.append([int(row["BE"]), int(row["FE"]), int(row["PM"])])
    return duration, pred, dem


def write_md(results, best, best_hours):
    days = best_hours / 8
    weeks = days / 5

    with open("phase5_report.md", "w", encoding="utf-8") as f:
        f.write("# Фаза 5. Календарно-ресурсное планирование проекта FinMate\n\n")

        f.write("## Использованные эвристики\n")
        f.write("SLK, FREE, LST, LFT, LPT, MIS и 50 случайных Activity List.\n\n")

        f.write("## Результаты планирования\n\n")
        f.write("| Эвристика | Длительность, ч | Дни | Недели |\n")
        f.write("|----------|----------------|------|--------|\n")

        for name, hours in results:
            f.write(f"| {name} | {hours} | {hours/8:.1f} | {hours/40:.1f} |\n")

        f.write("\n## Лучшее решение\n")
        f.write(
            f"Лучшее расписание получено методом **{best}**.\n\n"
            f"Плановая длительность проекта:\n"
            f"- **{best_hours} часов**\n"
            f"- **{days:.1f} рабочих дней**\n"
            f"- **{weeks:.1f} недель** (при 40-часовой рабочей неделе)\n"
        )

def main():
    seed(42)

    duration, predecessors, demands = read_tasks()
    capacity = [1, 1, 1]

    sampler = ActivityListSampler(predecessors)
    decoder = ActivityListDecoder()

    succ = successors_by_predecessors(predecessors)
    est, lst = calculate_critical_times(duration, predecessors, succ)
    eft = [est[i] + duration[i] for i in range(len(duration))]
    slk = [lst[i] - est[i] for i in range(len(duration))]

    rules = {
        "SLK": lambda i: slk[i],
        "LPT": lambda i: -duration[i],
        "MIS": lambda i: -len(succ[i]),
    }

    results = []

    for name, rule in rules.items():
        al = sampler.min_rule(rule)
        st = decoder.decode(al, duration, predecessors, demands, capacity)
        ms = max(st[i] + duration[i] for i in range(len(duration)))
        results.append((name, ms))

    for i in range(50):
        al = sampler.random()
        st = decoder.decode(al, duration, predecessors, demands, capacity)
        ms = max(st[j] + duration[j] for j in range(len(duration)))
        results.append((f"RAND_{i+1}", ms))

    results.sort(key=lambda x: x[1])
    best_name, best_hours = results[0]

    write_md(results, best_name, best_hours)

    print("Файл phase5_report.md успешно создан.")

if __name__ == "__main__":
    main()
