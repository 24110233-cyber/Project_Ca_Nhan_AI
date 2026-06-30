# -*- coding: utf-8 -*-

def format_assignment(assignment, names):
    parts = [f"'{names[k]} ({k})': '{v}'" for k, v in assignment.items()]
    return "{" + ", ".join(parts) + "}"

def forward_checking_search(variables, domains, neighbors, names):
    """
    Forward Checking Search generator for CSP Map Coloring.
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
        
        # We only try colors that are currently in the domain of var
        available_colors = list(current_domains[var])
        for val in available_colors:
            yield "try_val", assignment.copy(), {v: list(current_domains[v]) for v in variables}, var, val, f" - Thử gán {var_name} ({var}) = {val}"
            
            # Assignment is consistent with previous nodes because of Forward Checking pruning
            assignment[var] = val
            
            # Save domain state before pruning
            prev_domains = {v: list(current_domains[v]) for v in variables}
            current_domains[var] = [val]
            
            # Prune domains of unassigned neighbors
            pruned_info = []
            empty_domain_found = False
            failed_neighbor = None
            
            for neighbor in neighbors[var]:
                if neighbor not in assignment:
                    if val in current_domains[neighbor]:
                        current_domains[neighbor].remove(val)
                        pruned_info.append((neighbor, list(current_domains[neighbor])))
                        if len(current_domains[neighbor]) == 0:
                            empty_domain_found = True
                            failed_neighbor = neighbor
            
            yield "assign", assignment.copy(), {v: list(current_domains[v]) for v in variables}, var, val, f"   -> Hợp lệ. Assignment = {format_assignment(assignment, names)}"
            
            if pruned_info:
                # Log domain updates
                log_msg = "   -> Cập nhật domain các huyện/quận giáp ranh chưa gán:"
                for n, dom in pruned_info:
                    n_name = names.get(n, n)
                    dom_str = ", ".join([f"'{c}'" for c in dom])
                    log_msg += f"\n     + Miền giá trị của {n_name} ({n}) = [{dom_str}]"
                yield "prune", assignment.copy(), {v: list(current_domains[v]) for v in variables}, var, val, log_msg
                
            if empty_domain_found:
                failed_name = names.get(failed_neighbor, failed_neighbor)
                yield "conflict", assignment.copy(), {v: list(current_domains[v]) for v in variables}, var, val, f"   -> Thất bại: Miền giá trị của {failed_name} ({failed_neighbor}) bị rỗng! Cần quay lui."
                # Restore domains
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
