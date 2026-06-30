# -*- coding: utf-8 -*-

def format_assignment(assignment, names):
    parts = [f"'{names[k]} ({k})': '{v}'" for k, v in assignment.items()]
    return "{" + ", ".join(parts) + "}"

def backtracking_search(variables, domains, neighbors, names):
    """
    Backtracking Search generator for CSP Map Coloring.
    Yields: (step_type, assignment, current_domains, current_var, current_val, log_message)
    """
    assignment = {}
    # Classic backtracking does not prune domains in advance, 
    # but we track the domain of each variable to show in the GUI.
    # Initially all domains are full.
    current_domains = {v: list(domains[v]) for v in variables}
    
    # We will use a mutable step counter passed inside a list
    step_num = [0]
    
    def backtrack():
        if len(assignment) == len(variables):
            yield "success", assignment.copy(), {v: list(current_domains[v]) for v in variables}, None, None, "Tìm thấy lời giải thành công!"
            return True
            
        # Select first unassigned variable
        var = None
        for v in variables:
            if v not in assignment:
                var = v
                break
        
        step_num[0] += 1
        var_name = names.get(var, var)
        yield "select_var", assignment.copy(), {v: list(current_domains[v]) for v in variables}, var, None, f"Bước {step_num[0]}: Chọn quận/huyện để tô: {var_name} ({var})"
        
        for val in domains[var]:
            yield "try_val", assignment.copy(), {v: list(current_domains[v]) for v in variables}, var, val, f" - Thử gán {var_name} ({var}) = {val}"
            
            # Check consistency
            consistent = True
            conflict_neighbor = None
            for neighbor in neighbors[var]:
                if neighbor in assignment and assignment[neighbor] == val:
                    consistent = False
                    conflict_neighbor = neighbor
                    break
            
            if not consistent:
                conflict_name = names.get(conflict_neighbor, conflict_neighbor)
                yield "conflict", assignment.copy(), {v: list(current_domains[v]) for v in variables}, var, val, f"   -> Thất bại: Trùng màu với {conflict_name} ({conflict_neighbor})"
                continue
                
            # Consistent assignment
            assignment[var] = val
            # For visualization, we set the domain of the assigned variable to just the assigned color
            old_domains = {v: list(current_domains[v]) for v in variables}
            current_domains[var] = [val]
            
            yield "assign", assignment.copy(), {v: list(current_domains[v]) for v in variables}, var, val, f"   -> Hợp lệ. Assignment = {format_assignment(assignment, names)}"
            
            result = yield from backtrack()
            if result:
                return True
                
            # Backtrack
            del assignment[var]
            current_domains.update(old_domains)
            yield "backtrack", assignment.copy(), {v: list(current_domains[v]) for v in variables}, var, val, f"   -> Quay lui: Bỏ gán {var_name} ({var}) (thử màu khác hoặc lùi lại)"
            
        return False

    yield from backtrack()
