import re
import subprocess as sub
# This is a comment

def run_command(cmd):
    pipe = sub.Popen(cmd, shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
    stdout, stderr = pipe.communicate()
    return stdout

####################################################
def calc_dop_orb(prm_file):
    ##### COMPUTE DOPPLER AND UPDATE PRM FILE #####
    log_file = os.path.splitext(prm_file)[0] + '.log'
    output = gmtsarutils.run_command('calc_dop_orb ' + prm_file + ' ' + log_file + ' 0 0')
    log_out = open(log_file).readlines()
    PRM = open(prm_file, 'a')
    for line in log_out:
        PRM.write(line)
    PRM.close()
    os.remove(log_file)

####################################################
def read_prm(prm_file):
  prm_dict = {}
  for line in open(prm_file):
    c = line.split("=")
    if len(c) < 2 or line.startswith('%') or line.startswith('#'): 
      next #ignore commented lines or those without variables
    else: 
      prm_dict[c[0].strip()] = str.replace(c[1], '\n', '').strip()
  return prm_dict
####################################################
def update_prm(file, param, value):
  output = open(file).readlines()
  f = open(file, 'w')
  match = False
  for line in output:
    c = line.split("=")
    l__match = re.match(param, c[0].strip())
    if l__match:
      match = True
      f.write('%-23s = %s\n' % (param, value))
    else:
      f.write(line)
  if not match:
    f.write('%-23s = %s\n' % (param, value))
  f.close() 
####################################################
