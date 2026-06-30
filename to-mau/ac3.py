# -*- coding: utf-8 -*-

def format_assignment(assignment, names):
    parts = [f"'{names[k]} ({k})': '{v}'" for k, v in assignment.items()]
    return "{" + ", ".join(parts) + "}"

def ac3_search(variables, domains, neighbors, names):
    """
    Backtracking Search with AC-3 constraint propagation (MAC) generator for CSP Map Coloring.
    Yields: (step_type, assignment, current_domains, current_var, current_val, log_message)
    """
    assignment = {}
    current_domains = {v: list(domains[v]) for v in variables}
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
        
        # Try each color currently in the variable's domain
        available_colors = list(current_domains[var])
        for val in available_colors:
            yield "try_val", assignment.copy(), {v: list(current_domains[v]) for v in variables}, var, val, f" - Thử gán {var_name} ({var}) = {val}"
            
            # Save domain state before assignment and pruning
            prev_domains = {v: list(current_domains[v]) for v in variables}
            
            # Assign value
            assignment[var] = val
            current_domains[var] = [val]
            
            yield "assign", assignment.copy(), {v: list(current_domains[v]) for v in variables}, var, val, f"   -> Hợp lệ. Assignment = {format_assignment(assignment, names)}"
            
            # Run AC-3 constraint propagation
            # Queue initially contains all arcs (Xk, var) where Xk is an unassigned neighbor of var
            queue = [(neighbor, var) for neighbor in neighbors[var] if neighbor not in assignment]
            
            ac3_failed = False
            pruned_info = []
            failed_var = None
            
            while queue:
                xi, xj = queue.pop(0)
                
                # RM-Inconsistent-Values(Xi, Xj)
                removed = False
                new_domain_xi = []
                for x in current_domains[xi]:
                    # Check if there is any value y in Domain[Xj] that satisfies the constraint (x != y)
                    has_support = False
                    for y in current_domains[xj]:
                        if x != y:
                            has_support = True
                            break
                    if has_support:
                        new_domain_xi.append(x)
                    else:
                        removed = True
                
                if removed:
                    current_domains[xi] = new_domain_xi
                    pruned_info.append((xi, list(new_domain_xi)))
                    
                    if len(current_domains[xi]) == 0:
                        ac3_failed = True
                        failed_var = xi
                        break
                    
                    # Since Domain[Xi] was reduced, add all arcs (Xk, Xi) to queue
                    # where Xk is an unassigned neighbor of Xi and Xk != Xj
                    for xk in neighbors[xi]:
                        if xk not in assignment and xk != xj:
                            # Avoid duplicates in queue
                            if (xk, xi) not in queue:
                                queue.append((xk, xi))
            
            if pruned_info:
                log_msg = "   -> AC-3 Lan truyền ràng buộc (Arc Consistency):"
                for n, dom in pruned_info:
                    n_name = names.get(n, n)
                    dom_str = ", ".join([f"'{c}'" for c in dom])
                    log_msg += f"\n     + Cắt tỉa miền giá trị của {n_name} ({n}) = [{dom_str}]"
                yield "prune", assignment.copy(), {v: list(current_domains[v]) for v in variables}, var, val, log_msg
                
            if ac3_failed:
                failed_name = names.get(failed_var, failed_var)
                yield "conflict", assignment.copy(), {v: list(current_domains[v]) for v in variables}, var, val, f"   -> Thất bại: AC-3 phát hiện miền giá trị của {failed_name} ({failed_var}) bị rỗng! Cần quay lui."
                
                # Restore domains and assignment
                current_domains.clear()
                current_domains.update(prev_domains)
                del assignment[var]
                yield "backtrack", assignment.copy(), {v: list(current_domains[v]) for v in variables}, var, val, f"   -> Quay lui: Bỏ gán {var_name} ({var}) và khôi phục domain"
                continue
            
            # Recurse
            result = yield from backtrack()
            if result:
                return True
                
            # Restore domains and backtrack if recursion fails
            current_domains.clear()
            current_domains.update(prev_domains)
            del assignment[var]
            yield "backtrack", assignment.copy(), {v: list(current_domains[v]) for v in variables}, var, val, f"   -> Quay lui: Bỏ gán {var_name} ({var}) và khôi phục domain"
            
        return False

    yield from backtrack()
