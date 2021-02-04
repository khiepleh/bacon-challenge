from graph.parse_movies import Graph


def base_cases(graph: Graph, root: str, target: str):
    """Checks the base cases for a graph search: root == target and root and/or target don't exist in the graph.

    Returns:
    0 if root == target
    -1 if !root
    -2 if !target
    -3 if !root and !target
    """
    if root == target:
        return 0

    def check_presence(actor: str):
        try:
            graph[actor]
            return True
        except KeyError:
            return False

    a = check_presence(root)
    b = check_presence(target)

    if not a and not b: return -3
    if not b:           return -2
    if not a:           return -1

    return 1


def bfs(graph: Graph, root: str, target: str):
    """Perform two sided BFS to find the shortest path between root and target.
    """
    base = base_cases(graph, root, target)
    if base <= 0: return base

    # The queues are for enforcing visitation order.
    # The dicts are for quickly checking the other queue for intersections and
    # subsequently fetching the corresponding depth because of their constant time access.
    queue_root   = [(root, 0)]
    dict_root    = {root : 0}

    queue_target = [(target, 0)]
    dict_target  = {target : 0}

    visited = set([root, target])

    def check_neighbours(neighbours: set, depth: int, dest: str, q_src: list, d_src: dict, check: dict):
        best = None
        for neighbour in neighbours:
            if neighbour == dest:
                return depth

            # Check if there's an intersection - i.e. the other BFS has already queued up
            # the neighbour we're currently visiting. Still need to check the other
            # neighbours to ensure the optimal solution.
            if neighbour in check.keys():
                length = check[neighbour] + depth
                if best is None or best > length:
                    best = length

            if neighbour not in visited:
                visited.add(neighbour)
                q_src.append((neighbour, depth))
                d_src[neighbour] = depth

        return best

    while queue_root and queue_target:
        best = None

        orig_depth = queue_root[0][1]
        next_depth = orig_depth

        # The inner loops are required to find the optimal path - see the test cases for
        # an example which can return a sub-optimal depth without this logic.
        while orig_depth == next_depth:
            actor, depth = queue_root.pop(0)
            depth += 1
            check = check_neighbours(graph[actor], depth, target, queue_root, dict_root, dict_target)
            if check is not None:
                best = check if best is None else min(check, best)

            try:
                next_depth = queue_root[0][1]
            except IndexError:
                break

        orig_depth = queue_target[0][1]
        next_depth = orig_depth
        while orig_depth == next_depth:
            actor, depth = queue_target.pop(0)
            depth += 1
            check = check_neighbours(graph[actor], depth, root, queue_target, dict_target, dict_root)
            if check is not None:
                best = check if best is None else min(check, best)

            try:
                next_depth = queue_target[0][1]
            except IndexError:
                break

        if best is not None:
            return best
