import process_network_logs

with open('logs/test_dis_cur_ssh.txt', 'r', encoding='utf-8') as f:
    content = f.read()

print('Processing test_dis_cur_ssh.txt...')
result = process_network_logs.process_network_logs(content, output_dir='screenshots')
print(f'Generated {len(result)} screenshot(s):')
for r in result:
    print(f'  {r["screenshot_path"]}')
    print(f'    Commands: {r["commands_count"]}')
    print(f'    First router: {r["first_router"]}')
    print(f'    First command: {r["first_command"]}')
