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
del node1
del node2

# The objects are not freed by reference counting alone. The garbage collector will eventually collect them.
