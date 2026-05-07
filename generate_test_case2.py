from process_network_logs import main
import asyncio

# Generate standalone PNG for Case 1 (no SSH, no username)
log_content = """<TUCxx01>display current-configuration
!
sysname TUCxx01
#
return
"""

with open('logs/test_case2_simple.txt', 'w', encoding='utf-8') as f:
    f.write(log_content)

asyncio.run(main(['logs/test_case2_simple.txt']))
print("Generated standalone dis cur PNG")
