from graph.parse_movies import Graph

from sortedcontainers import SortedList


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
    """DEPRECATED: A super basic breadth-first-search using Python builtins. Very slow."""

    base = base_cases(graph, root, target)
    if base <= 0: return base

    queue   = [(root, 0)]
    visited = [root]

    while queue:
        curr_actor, depth = queue.pop(0)
        depth += 1

        for neighbour in graph[curr_actor]:
            if neighbour == target:
                return depth

            if neighbour not in visited:
                visited.append(neighbour)
                queue.append((neighbour, depth))


def bfs_with_sort(graph: Graph, root: str, target: str):
    """DEPRECATED: A breadth-first-search which sorts actor lists to improve individual search times.

    This is much faster than pure BFS, but still notably slower than using a pre-sorted Graph (SortedGraph).
    """
    base = base_cases(graph, root, target)
    if base <= 0: return base

    queue   = [(root, 0)]
    visited = SortedList([root])

    while queue:
        curr_actor, depth = queue.pop(0)
        depth += 1

        neighbours = SortedList(graph[curr_actor])

        if target in neighbours:
            return depth

        for neighbour in neighbours:
            if neighbour not in visited:
                visited.add(neighbour)
                queue.append((neighbour, depth))


def bfs_pre_sorted(graph, root: str, target: str):
    """Do a breadth-first-search on graph, starting at root and ending at target. Return the depth (i.e. length of path from root to target).

    Makes use of sortedcontainers.SortedList for speed - it's notably faster this way.
    """
    base = base_cases(graph, root, target)
    if base <= 0: return base

    queue   = [(root, 0)]
    visited = SortedList([root])

    while queue:
        curr_actor, depth = queue.pop(0)
        depth += 1

        neighbours = graph[curr_actor]

        if target in neighbours:
            return depth

        for neighbour in neighbours:
            if neighbour not in visited:
                visited.add(neighbour)
                queue.append((neighbour, depth))

    # The horror! Callers need to handle "None", as well.
