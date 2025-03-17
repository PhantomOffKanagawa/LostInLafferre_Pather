from collections import defaultdict

def merge_polylines(polylines):
    # Step 1: Build adjacency list
    adjacency = defaultdict(set)
    coord_to_lines = defaultdict(set)

    for i, polyline in enumerate(polylines):
        for coord in polyline:
            coord_to_lines[coord].add(i)

    for indices in coord_to_lines.values():
        indices = list(indices)
        for i in range(len(indices)):
            for j in range(i + 1, len(indices)):
                adjacency[indices[i]].add(indices[j])
                adjacency[indices[j]].add(indices[i])

    # Step 2: Find connected components
    visited = set()
    components = []

    def dfs(node, component):
        stack = [node]
        while stack:
            current = stack.pop()
            if current not in visited:
                visited.add(current)
                component.append(current)
                stack.extend(adjacency[current] - visited)

    for i in range(len(polylines)):
        if i not in visited:
            component = []
            dfs(i, component)
            components.append(component)

    # Step 3: Merge polylines in each component
    def merge_component(indices):
        all_coords = set()
        ordered_lines = []
        
        for idx in indices:
            ordered_lines.append(polylines[idx])
            all_coords.update(polylines[idx])

        # Attempt to chain polylines together
        merged = []
        while ordered_lines:
            current = ordered_lines.pop()
            if not merged:
                merged.append(current)
                continue

            for i, existing in enumerate(merged):
                if current[0] in existing:
                    merged[i] = current + existing[1:]
                    break
                elif current[-1] in existing:
                    merged[i] = existing + current[1:]
                    break
            else:
                merged.append(current)

        # Return longest merged polyline
        return max(merged, key=len)

    # Step 4: Return only the longest polylines
    longest_polylines = [merge_component(component) for component in components]
    return longest_polylines if longest_polylines else []