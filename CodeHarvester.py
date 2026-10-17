import re
import os
import sys

class CodeHarvester:
    # File scanning and extraction
    
    def __init__(self, root_path, output_path):
        self.root_path = root_path
        self.output_path = output_path
        
        # Check output directory existence
        if not os.path.exists(self.output_path):
            try:
                os.makedirs(self.output_path)
                print(f"[INFO] Directory created: '{self.output_path}'")
            except OSError as e:
                print(f"[ERROR] Could not create directory: {e}")
                sys.exit(1)
        else:
            print(f"[INFO] Saving to: '{self.output_path}'")

        # Exclude irrelevant folders
        self.ignore_folders = ['node_modules', '.git', 'android', 'ios', 'build', 'dist', '.expo']
        self.source_files = self._scan_files()
        print(f"[INIT] Project loaded. {len(self.source_files)} files identified.")

    def _scan_files(self):
        
        # Traverse project to return target file paths
        files_found = []
        if not os.path.exists(self.root_path):
            print("[ERROR] Project path does not exist!")
            return []

        for root, dirs, files in os.walk(self.root_path):
            # Modify dirs list in-place to avoid entering ignored folders
            dirs[:] = [d for d in dirs if d not in self.ignore_folders]
            
            for file in files:
                # Filter React specific files
                if file.endswith(('.js', '.jsx', '.ts', '.tsx')):
                    files_found.append(os.path.join(root, file))
        return files_found

    def _read_file(self, filepath):
       
        # Read file content and handle errors
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except:
            return ""

    def _save_to_file(self, filename, lines):
      
        # Write list to file
        full_path = os.path.join(self.output_path, filename)
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            
            abs_path = os.path.abspath(full_path)
            print(f"\n[SUCCESS] Report generated: {abs_path}")
        except Exception as e:
            print(f"[ERROR] Write failed: {e}")

#===========================================================================================================================
#--------------------------------------------------------COMMENTS REPORT----------------------------------------------------
#===========================================================================================================================

    def extract_comments(self):
        
        output = ["REPORT: COMMENTS (Clean Text)", "="*40, ""]
        regex = r'(/\*[\s\S]*?\*/|//.*)'
        
        total_project = 0
        for path in self.source_files:
            content = self._read_file(path)
            matches = re.findall(regex, content)
            
            cleaned_comments = []
            for m in matches:
                raw = m.strip()
                # Remove comment markers
                if raw.startswith('//'):
                    text = raw[2:].strip()
                elif raw.startswith('/*'):
                    text = raw[2:-2].strip()
                else:
                    text = raw.strip()
                
                # Keep relevant comments
                if len(text) > 5:
                    cleaned_comments.append(text)
            
            if cleaned_comments:
                count = len(cleaned_comments)
                total_project += count
                output.append(f"\nFile: {os.path.basename(path)} (Total: {count})")
                for txt in cleaned_comments:
                    output.append(f" - {txt}")
                    
        output.insert(2, f"GENERAL TOTAL COMMENTS: {total_project}\n")
        self._save_to_file("1_comments.txt", output)

#===========================================================================================================================
#--------------------------------------------------------DEPENDENCIES REPORT------------------------------------------------
#===========================================================================================================================

    def extract_imports(self):
        
        output = ["REPORT: DEPENDENCIES (IMPORTS)", "="*40, ""]
        
        # Modified regex: Captures complete line and path separately
        regex = r"(import\s+.*?\s+from\s+['\"](.*?)['\"];?)"
        
        total_project = 0
        unique_libs = set()     # External libraries
        unique_internal = set() # Local files
        
        for path in self.source_files:
            matches = re.findall(regex, self._read_file(path))
            
            if matches:
                count = len(matches)
                total_project += count
                output.append(f"\nFile: {os.path.basename(path)} (Total: {count})")
                
                for full_line, src in matches:
                    # Display full code line in detailed report
                    output.append(f" - {full_line.strip()}")
                    
                    # Classify for consolidated lists
                    if src.strip().startswith('.'):
                        unique_internal.add(src)
                    else:
                        unique_libs.add(src)
        
        output.insert(2, f"GENERAL TOTAL IMPORTS: {total_project}\n")
        
        output.append("\n" + "="*40)
        output.append(f"CONSOLIDATED LIST: EXTERNAL LIBRARIES ({len(unique_libs)}):")
        output.append("="*40)
        for lib in sorted(unique_libs):
            output.append(f" [LIB] {lib}")

        output.append("\n" + "="*40)
        output.append(f"CONSOLIDATED LIST: INTERNAL FILES ({len(unique_internal)}):")
        output.append("="*40)
        for int_file in sorted(unique_internal):
            output.append(f" [INT] {int_file}")

        self._save_to_file("2_imports.txt", output)

#===========================================================================================================================
#--------------------------------------------------------REPORT: COMPONENTS-------------------------------------------------
#===========================================================================================================================

    def extract_components(self):
       
        output = ["REPORT: UI COMPONENTS (React)", "="*40, ""]
        regex = r"(?:function\s+([A-Z][a-zA-Z0-9]*)|const\s+([A-Z][a-zA-Z0-9]*)\s*=\s*(?:async\s*)?\(|class\s+([A-Z][a-zA-Z0-9]*)\s+extends)"
        
        total_project = 0
        all_unique_comps = set() 
        
        for path in self.source_files:
            matches = re.findall(regex, self._read_file(path))
            # Extract only the found component name
            comps = [next(x for x in m if x) for m in matches]
            
            if comps:
                count = len(comps)
                total_project += count
                output.append(f"\nFile: {os.path.basename(path)} (Total: {count})")
                for c in comps:
                    # Display name only, without JSX symbols (< />)
                    output.append(f" [Comp] {c}")
                    all_unique_comps.add(c) 
                    
        output.insert(2, f"GENERAL TOTAL COMPONENT OCCURRENCES: {total_project}\n")
        
        output.append("\n" + "="*40)
        output.append(f"UNIQUE COMPONENTS INVENTORY ({len(all_unique_comps)} types):")
        output.append("="*40)
        for c in sorted(all_unique_comps):
            # Clean display in consolidated list
            output.append(f" - {c}")
        self._save_to_file("3_components.txt", output)

#===========================================================================================================================
#------------------------------------------------------------REPORT: TODO---------------------------------------------------
#===========================================================================================================================

    def extract_todos(self):
        
        output = ["REPORT: TODOs & TASKS", "="*40, ""]
        regex = r"(?://|/\*)\s*(TODO|FIXME):?\s*(.*?)(?:\*/|$)"
        
        total_project = 0
        for path in self.source_files:
            matches = re.findall(regex, self._read_file(path), re.MULTILINE)
            if matches:
                count = len(matches)
                total_project += count
                output.append(f"\nFile: {os.path.basename(path)} (Total: {count})")
                for tag, msg in matches: 
                    output.append(f" [!] {tag}: {msg.strip()}")
        
        output.insert(2, f"GENERAL TOTAL TODOs: {total_project}\n")
        self._save_to_file("4_todos.txt", output)


#===========================================================================================================================
#--------------------------------------------------------REPORT: STATE VARIABLES--------------------------------------------
#===========================================================================================================================
    def extract_states(self):
        
        output = ["REPORT: STATE VARIABLES (useState)", "="*40, ""]
        regex = r"const\s*\[\s*(\w+)\s*,.*?\]\s*=\s*useState"
        
        total_project = 0
        for path in self.source_files:
            states = re.findall(regex, self._read_file(path))
            if states:
                count = len(states)
                total_project += count
                output.append(f"\nFile: {os.path.basename(path)} (Total: {count})")
                for s in states:
                    output.append(f" - {s}")
                    
        output.insert(2, f"GENERAL TOTAL STATE VARIABLES: {total_project}\n")
        self._save_to_file("5_state_data.txt", output)

#===========================================================================================================================
#-------------------------------------------------------EXTRACT FUNCTIONS---------------------------------------------------
#===========================================================================================================================

    def extract_functions(self):
        
        output = ["REPORT: LIST OF FUNCTIONS AND METHODS", "="*40, ""]
        regex = r"(?:function\s+([a-zA-Z0-9_]+)|(?:const|let)\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?[\(\{])"
        
        total_project = 0
        all_unique_funcs = set() 
        
        for path in self.source_files:
            content = self._read_file(path)
            matches = re.findall(regex, content)
            
            funcs = []
            for m in matches:
                name = m[0] if m[0] else m[1]
                if name and name not in ['useState', 'useEffect', 'require']:
                    funcs.append(name)
            
            if funcs:
                count = len(funcs)
                total_project += count
                output.append(f"\nFile: {os.path.basename(path)} (Total: {count})")
                for f in funcs:
                    output.append(f"  [f] {f}()")
                    all_unique_funcs.add(f) 
                    
        output.insert(2, f"GENERAL TOTAL FUNCTION OCCURRENCES: {total_project}\n")
        
        output.append("\n" + "="*40)
        output.append(f"UNIQUE FUNCTIONS INVENTORY ({len(all_unique_funcs)} methods):")
        output.append("="*40)
        for f in sorted(all_unique_funcs):
            output.append(f" - {f}()")
        self._save_to_file("6_functions_logic.txt", output)

#===========================================================================================================================
#-------------------------------------------------------ADVANCED ANALYSIS---------------------------------------------------
#===========================================================================================================================

    def extract_advanced_analysis(self):
        
        output = ["ADVANCED REPORT: CODE METRICS", "="*40, ""]
        
        regex_func = r"(?:function\s+([a-zA-Z0-9_]+)\s*\((.*?)\)|(?:const|let)\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\((.*?)\)\s*=>)"
        regex_complexity = r"\b(if|else|for|while|switch|case|catch|try)\b"
        
        total_funcs_project = 0
        for path in self.source_files:
            content = self._read_file(path)
            
            decisions = len(re.findall(regex_complexity, content))
            complexity_score = decisions + 1
            
            complexity_rating = "LOW"
            if complexity_score > 10: complexity_rating = "MEDIUM"
            if complexity_score > 20: complexity_rating = "HIGH"
            
            matches = re.findall(regex_func, content)
            file_funcs = []
            
            for m in matches:
                if m[0]: 
                    name = m[0]
                    params_raw = m[1]
                else: 
                    name = m[2]
                    params_raw = m[3]
                
                if name and name not in ['useState', 'useEffect', 'require']:
                    params = [p.strip() for p in params_raw.split(',') if p.strip()]
                    file_funcs.append({
                        "name": name,
                        "params": params,
                        "args_count": len(params)
                    })
            
            if file_funcs:
                count = len(file_funcs)
                total_funcs_project += count
                filename = os.path.basename(path)
                
                output.append(f"\n------------")
                output.append(f"FILE: {filename}")
                output.append(f"COMPLEXITY SCORE: {complexity_score} ({complexity_rating})")
                output.append(f"DETAILED FUNCTIONS: {count}")
                
                for f in file_funcs:
                    param_str = ", ".join(f['params']) if f['params'] else "void"
                    output.append(f"  [f] {f['name']}({param_str}) - {f['args_count']} args")
                    
        output.insert(2, f"TOTAL FUNCTIONS ANALYZED: {total_funcs_project}\n")
        self._save_to_file("7_advanced_analysis.txt", output)

#===========================================================================================================================
#--------------------------------------------------------MAIN---------------------------------------------------------------
#===========================================================================================================================
def main():
    print("="*50)
    print("    REACT NATIVE DOCUMENTATION GENERATOR    ")
    print("="*50)
    
    path_input = input("\n[INPUT] Enter the PROJECT folder path: ").strip().strip('"')
    if not path_input: path_input = "." 
    
    path_output = input("[OUTPUT] Enter the folder to save REPORTS (default: 'rapoarte_proiect'): ").strip().strip('"')
    if not path_output: path_output = "rapoarte_proiect"

    harvester = CodeHarvester(path_input, path_output)

    while True:
        print("\n--- OPTIONS MENU ---")
        print("1. Extract Comments")
        print("2. Extract Imports")
        print("3. Extract Components")
        print("4. Extract TODOs")
        print("5. Extract STATE")
        print("6. Extract Functions")
        print("7. Advanced Analysis")
        print("0. Exit")
        
        opt = input("\n>> Your option: ")

        if opt == '1': harvester.extract_comments()
        elif opt == '2': harvester.extract_imports()
        elif opt == '3': harvester.extract_components()
        elif opt == '4': harvester.extract_todos()
        elif opt == '5': harvester.extract_states()
        elif opt == '6': harvester.extract_functions()
        elif opt == '7': harvester.extract_advanced_analysis()
        elif opt == '0': break
        else: print("Invalid option!")

if __name__ == "__main__":
    main()