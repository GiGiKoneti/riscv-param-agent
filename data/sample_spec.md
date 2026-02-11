# Chapter 3: Machine-Level ISA

This chapter describes the machine-level ISA for RISC-V processors.

## 3.1 Machine-Mode CSRs

The machine mode includes several Control and Status Registers (CSRs) that control various aspects of the processor.

### 3.1.1 Machine Status Register (mstatus)

The mstatus register is an MXLEN-bit read/write register that tracks and controls the hart's current operating state. The MIE bit in mstatus is a global interrupt-enable bit for machine mode.

### 3.1.2 Machine Trap-Vector Base-Address Register (mtvec)

The mtvec register is an MXLEN-bit read/write register that holds trap vector configuration, consisting of a vector base address (BASE) and a vector mode (MODE).

## 3.2 CSR Address Space

The standard RISC-V ISA sets aside a 12-bit encoding space (csr[11:0]) for up to 4,096 CSRs. By convention, the upper 4 bits of the CSR address (csr[11:8]) are used to encode the read and write accessibility of the CSRs according to privilege level.

## 3.3 Physical Memory Attributes

### 3.3.1 Cache Organization

Caches organize copies of data into cache blocks, each of which represents a contiguous, naturally aligned power-of-two (or NAPOT) range of memory locations. The capacity and organization of a cache and the size of a cache block are both implementation-specific.

### 3.3.2 Physical Memory Protection

Implementations may implement zero, 16, or 64 PMP entries. The number of PMP entries is implementation-defined.

## 3.4 Reset Behavior

On reset, the program counter (pc) is set to an implementation-defined reset vector. The reset vector address is implementation-specific and may vary between different RISC-V implementations.

## 3.5 Machine Architecture ID

The marchid CSR is a MXLEN-bit read-only register encoding the base microarchitecture of the hart. The value returned in marchid is implementation-defined.
