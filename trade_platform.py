from acct import Ledger
print('Ledger class imported')

data1 = [ 1, 1, "2018-05-03", "Test Event JE 1", "Investments", "Chequing", "100"]
data2 = [ 2, 1, "2018-05-04", "Test Event JE 2", "Chequing", "Investments", "100"]
print('Data setup.')

event1 = [data1, data2]
print('Event setup.')

ledger = Ledger('test_1')
print('Ledger class loaded.')

#ledger.journal_entry(data1)
#print('Data1 Journal Entry booked')

print(event1)
ledger.journal_entry(event1)
print('Event1 loaded')