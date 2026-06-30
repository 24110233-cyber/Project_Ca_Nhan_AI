# -*- coding: utf-8 -*-
import random

def min_conflicts_search(variables, domains, neighbors, names, max_steps=150):
    """
    Min-Conflicts Search generator for CSP Map Coloring.
    Yields: (step_type, assignment, current_domains, current_var, current_val, log_message)
    """
    # Helper to count conflicts for a variable with a specific value
    def count_conflicts(var, val, current_assignment):
        conflicts = 0
        for n in neighbors[var]:
            if n in current_assignment and current_assignment[n] == val:
                conflicts += 1
        return conflicts

    # Helper to get all conflicted variables
    def get_conflicted_variables(current_assignment):
        conflicted = []
        for var in variables:
            val = current_assignment[var]
            for n in neighbors[var]:
                if current_assignment[n] == val:
                    conflicted.append(var)
                    break
        return conflicted

    # Helper to calculate total conflicts in assignment
    def get_total_conflicts(current_assignment):
        total = 0
        for var in variables:
            val = current_assignment[var]
            for n in neighbors[var]:
                if current_assignment[n] == val:
                    total += 1
        return total // 2

    # Step 0: Initial complete assignment
    # We assign a random color from the variable's domain to each variable
    assignment = {}
    for var in variables:
        assignment[var] = random.choice(domains[var])
        
    current_domains = {v: list(domains[v]) for v in variables}
    
    total_conf = get_total_conflicts(assignment)
    yield "assign", assignment.copy(), current_domains, None, None, f"Khởi tạo cấu hình ban đầu ngẫu nhiên. Số xung đột ban đầu = {total_conf}"
    
    for step in range(1, max_steps + 1):
        conflicted_vars = get_conflicted_variables(assignment)
        total_conf_real = get_total_conflicts(assignment)
        
        if total_conf_real == 0:
            yield "success", assignment.copy(), current_domains, None, None, f"Tìm thấy lời giải thành công ở bước {step}! Số xung đột = 0."
            return True
            
        # Choose a conflicted variable randomly
        var = random.choice(conflicted_vars)
        var_name = names.get(var, var)
        
        yield "select_var", assignment.copy(), current_domains, var, None, f"Bước {step}: Chọn ngẫu nhiên biến bị xung đột: {var_name} ({var})"
        
        # Find the value that minimizes conflicts
        current_val = assignment[var]
        min_conf = float('inf')
        best_vals = []
        
        log_try = f" - Đang xét các màu cho {var_name} ({var}):"
        for val in domains[var]:
            c = count_conflicts(var, val, assignment)
            log_try += f"\n     + Màu {val}: {c} xung đột"
            if c < min_conf:
                min_conf = c
                best_vals = [val]
            elif c == min_conf:
                best_vals.append(val)
                
        yield "try_val", assignment.copy(), current_domains, var, None, log_try
        
        # Choose one value that minimizes conflicts
        # Prefer a different value from the current one if it has the same min_conf (to avoid getting stuck)
        other_bests = [v for v in best_vals if v != current_val]
        if other_bests:
            chosen_val = random.choice(other_bests)
        else:
            chosen_val = current_val
            
        # Update assignment
        assignment[var] = chosen_val
        
        # Log the change
        if chosen_val == current_val:
            log_msg = f"   -> Giữ nguyên màu '{chosen_val}' cho {var_name} ({var}) vì nó tối thiểu hóa xung đột ({min_conf} xung đột)"
        else:
            log_msg = f"   -> Thay đổi {var_name} ({var}) từ màu '{current_val}' sang màu '{chosen_val}' để giảm xung đột xuống {min_conf}"
            
        yield "assign", assignment.copy(), current_domains, var, chosen_val, log_msg
        
    yield "conflict", assignment.copy(), current_domains, None, None, f"Thất bại: Đạt giới hạn max_steps ({max_steps}) mà không tìm thấy lời giải không có xung đột!"
    return False
