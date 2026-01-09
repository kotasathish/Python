class Node:
    def __init__(self, value):
        self.value = value
        self.next = None

# Create nodes that point to each other forming a cycle
node1 = Node(1)
node2 = Node(2)
node1.next = node2
node2.next = node1

def has_cycle(head: Node) -> bool:
    slow = head
    fast = head
    print("Hi!")

    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next

        if slow == fast:
            return True

    return False
# Example usage:
print(has_cycle(node1))  # Output: True
print("Hello, World!")

# Now, even if we remove the external references, the reference count for each node is 1 (they reference each other)
#del node1
#del node2

# The objects are not freed by reference counting alone. The garbage collector will eventually collect them.

#Reference Counting (Primary Mechanism)
#Example:
a = [1, 2, 3]  # Reference count = 1 (assigned to `a`)
b = a          # Reference count = 2 (`b` points to the same list)
del a          # Reference count = 1 (only `b` remains)
b = None       # Reference count = 0 → Memory freed!

#reference cycle example
# Delete external references
del node1, node2

#Handle Cycles Manually:
#	Option 1: Explicitly break references when done:
node1.next = None  # Break the cycle before deletion
node2.next = None

#	Option 2: Use weakref for non-owning references:
import weakref
node2.next = weakref.ref(node1)  # Doesn't increase reference count!

#	Option 3: Force garbage collection:
import gc
gc.collect()  # Manually trigger cycle detection