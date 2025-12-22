#!/usr/bin/env python3
"""
VALIDAÇÃO DE WORKFLOWS - Verifica independência e configurações corretas
"""

import re
from pathlib import Path

def extract_schedule(yml_content: str) -> str:
    """Extrai cron schedule do workflow (ignora linhas comentadas)"""
    # Procura por linhas com cron que NÃO comecem com #
    lines = yml_content.split('\n')
    for line in lines:
        stripped = line.strip()
        # Ignora comentários
        if stripped.startswith('#'):
            continue
        # Busca cron:
        if 'cron:' in line:
            match = re.search(r'cron:\s*["\']([^"\']+)["\']', line)
            return match.group(1) if match else "INVALID CRON"
    return "NO SCHEDULE"

def extract_script(yml_content: str) -> str:
    """Extrai script python executado"""
    match = re.search(r'python\s+([^\s\\]+\.py)', yml_content)
    return match.group(1) if match else "NO SCRIPT"

def extract_concurrency(yml_content: str) -> str:
    """Extrai concurrency group"""
    match = re.search(r'group:\s*([^\s]+)', yml_content)
    return match.group(1) if match else "NO GROUP"

def check_workflow(path: Path) -> dict:
    """Analisa um workflow e retorna suas características"""
    content = path.read_text()
    
    # Detecta se schedule está ativo (não comentado)
    has_active_schedule = False
    for line in content.split('\n'):
        stripped = line.strip()
        if not stripped.startswith('#') and 'cron:' in line:
            has_active_schedule = True
            break
    
    return {
        "name": path.stem,
        "schedule": extract_schedule(content),
        "script": extract_script(content),
        "concurrency": extract_concurrency(content),
        "has_schedule": has_active_schedule,
    }

def main():
    workflows_dir = Path("/home/claude/.github/workflows")
    
    if not workflows_dir.exists():
        print("❌ Diretório .github/workflows não encontrado")
        return
    
    workflows = sorted(workflows_dir.glob("*.yml"))
    
    if not workflows:
        print("❌ Nenhum workflow encontrado")
        return
    
    print("=" * 80)
    print("VALIDAÇÃO DE WORKFLOWS - INDEPENDÊNCIA")
    print("=" * 80)
    print()
    
    results = []
    
    for wf in workflows:
        info = check_workflow(wf)
        results.append(info)
        
        status = "✅ ATIVO" if info["has_schedule"] else "⏸️  MANUAL"
        
        print(f"📄 {info['name']}")
        print(f"   Schedule:    {info['schedule']} {status}")
        print(f"   Script:      {info['script']}")
        print(f"   Concurrency: {info['concurrency']}")
        print()
    
    print("=" * 80)
    print("VERIFICAÇÕES DE INDEPENDÊNCIA")
    print("=" * 80)
    print()
    
    # Check 1: Concurrency groups únicos
    groups = [r["concurrency"] for r in results]
    if len(groups) == len(set(groups)):
        print("✅ Concurrency groups são únicos (sem conflito de locks)")
    else:
        print("❌ ERRO: Concurrency groups duplicados detectados")
    print()
    
    # Check 2: Scripts únicos ou desabilitados
    active_scripts = [(r["name"], r["script"]) for r in results if r["has_schedule"]]
    scripts_only = [s for _, s in active_scripts]
    
    if len(scripts_only) == len(set(scripts_only)):
        print("✅ Workflows ativos executam scripts únicos (sem duplicação)")
    else:
        print("⚠️  AVISO: Múltiplos workflows ativos executam o mesmo script")
    
    for name, script in active_scripts:
        print(f"   - {name}: {script}")
    print()
    
    # Check 3: Schedules escalonados
    active_schedules = [(r["name"], r["schedule"]) for r in results if r["has_schedule"]]
    
    if len(active_schedules) > 1:
        schedules_only = [s for _, s in active_schedules]
        if len(schedules_only) == len(set(schedules_only)):
            print("✅ Schedules escalonados (horários diferentes)")
        else:
            print("❌ ERRO: Workflows rodando no MESMO horário detectados")
        
        for name, schedule in active_schedules:
            print(f"   - {name}: {schedule}")
    print()
    
    # Check 4: Workflow "all" deve estar desabilitado
    all_wf = next((r for r in results if "balancos" in r["name"]), None)
    
    if all_wf:
        if not all_wf["has_schedule"]:
            print("✅ Workflow 'normalizar_balancos' desabilitado (evita conflito)")
        else:
            print("❌ ERRO: Workflow 'normalizar_balancos' ATIVO (vai conflitar com individuais)")
    print()
    
    # Check 5: Separação por demonstração
    print("=" * 80)
    print("MAPEAMENTO WORKFLOW → DEMONSTRAÇÃO")
    print("=" * 80)
    print()
    
    for r in results:
        demo = "TODAS" if "all" in r["script"] else r["name"].replace("normalizar_", "").upper()
        status = "ATIVO" if r["has_schedule"] else "MANUAL"
        print(f"{status:8} | {r['name']:25} → {demo}")
    
    print()
    print("=" * 80)
    
    # Resumo final
    active_count = sum(1 for r in results if r["has_schedule"])
    manual_count = len(results) - active_count
    
    print()
    print(f"📊 RESUMO:")
    print(f"   Total workflows: {len(results)}")
    print(f"   Ativos (schedule): {active_count}")
    print(f"   Manuais (dispatch): {manual_count}")
    print()
    
    # Recomendações
    print("💡 RECOMENDAÇÕES:")
    
    if all_wf and all_wf["has_schedule"]:
        print("   ⚠️  DESABILITE o schedule do normalizar_balancos.yml")
        print("      Workflows individuais são suficientes e evitam conflitos")
    
    conflicts = [s for s in schedules_only if schedules_only.count(s) > 1]
    if conflicts:
        print("   ⚠️  ESCALONE os horários dos workflows ativos")
        print("      Sugestão: 3:15 AM (DRE), 3:25 AM (BPA/BPP), 3:35 AM (DFC)")
    
    if active_count == 0:
        print("   ⚠️  Nenhum workflow com schedule ativo")
        print("      Habilite workflows individuais ou o 'all' (não ambos)")
    
    print()

if __name__ == "__main__":
    main()
