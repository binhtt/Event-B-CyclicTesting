# Event-B source listing (rendered from native XML)

The native Rodin project is authoritative. This listing is for reading only.

## C_AutomotivePilot

```text
carrierSet POS
carrierSet MODE
constant pNeutral
constant pLeft
constant pRight
constant noMode
constant leftMode
constant rightMode
constant bothMode
constant period
constant ticks
constant command
constant lampL
constant lampR
axiom partition(POS, {pNeutral}, {pLeft}, {pRight})
axiom partition(MODE, {noMode}, {leftMode}, {rightMode}, {bothMode})
axiom period ∈ ℕ1 ∧ period = 100
axiom ticks ∈ ℕ1 ∧ ticks = 5
axiom period ∗ ticks = 500
axiom command ∈ ((BOOL × BOOL) × POS) → MODE
axiom command = {(((FALSE ↦ FALSE) ↦ pNeutral) ↦ noMode), (((FALSE ↦ FALSE) ↦ pLeft) ↦ noMode), (((FALSE ↦ FALSE) ↦ pRight) ↦ noMode), (((FALSE ↦ TRUE) ↦ pNeutral) ↦ bothMode), (((FALSE ↦ TRUE) ↦ pLeft) ↦ bothMode), (((FALSE ↦ TRUE) ↦ pRight) ↦ bothMode), (((TRUE ↦ FALSE) ↦ pNeutral) ↦ noMode), (((TRUE ↦ FALSE) ↦ pLeft) ↦ leftMode), (((TRUE ↦ FALSE) ↦ pRight) ↦ rightMode), (((TRUE ↦ TRUE) ↦ pNeutral) ↦ bothMode), (((TRUE ↦ TRUE) ↦ pLeft) ↦ bothMode), (((TRUE ↦ TRUE) ↦ pRight) ↦ bothMode)}
axiom lampL ∈ (MODE × BOOL) → {0, 100}
axiom lampL = {((noMode ↦ FALSE) ↦ 0), ((noMode ↦ TRUE) ↦ 0), ((leftMode ↦ FALSE) ↦ 0), ((leftMode ↦ TRUE) ↦ 100), ((rightMode ↦ FALSE) ↦ 0), ((rightMode ↦ TRUE) ↦ 0), ((bothMode ↦ FALSE) ↦ 0), ((bothMode ↦ TRUE) ↦ 100)}
axiom lampR ∈ (MODE × BOOL) → {0, 100}
axiom lampR = {((noMode ↦ FALSE) ↦ 0), ((noMode ↦ TRUE) ↦ 0), ((leftMode ↦ FALSE) ↦ 0), ((leftMode ↦ TRUE) ↦ 0), ((rightMode ↦ FALSE) ↦ 0), ((rightMode ↦ TRUE) ↦ 100), ((bothMode ↦ FALSE) ↦ 0), ((bothMode ↦ TRUE) ↦ 100)}
```

## M0_AtomicCycle

```text
seesContext C_AutomotivePilot
variable envE
variable envH
variable envP
variable obsE
variable obsH
variable obsP
variable active
variable on
variable remaining
variable blinkLeft
variable blinkRight
invariant envE ∈ BOOL
invariant envH ∈ BOOL
invariant envP ∈ POS
invariant obsE ∈ BOOL
invariant obsH ∈ BOOL
invariant obsP ∈ POS
invariant active ∈ MODE
invariant on ∈ BOOL
invariant remaining ∈ 0‥(ticks − 1)
invariant blinkLeft ∈ {0, 100}
invariant blinkRight ∈ {0, 100}
invariant active = command((obsE ↦ obsH) ↦ obsP)
invariant active = noMode ⇒ (on = FALSE ∧ remaining = 0)
invariant blinkLeft = lampL(active ↦ on)
invariant blinkRight = lampR(active ↦ on)
invariant obsH = TRUE ⇒ active = bothMode
invariant obsE = FALSE ∧ obsH = FALSE ⇒ active = noMode
invariant active = bothMode ⇒ blinkLeft = blinkRight
invariant on = FALSE ⇒ (blinkLeft = 0 ∧ blinkRight = 0)
invariant blinkLeft = 100 ⇒ active ∈ {leftMode, bothMode}
invariant blinkRight = 100 ⇒ active ∈ {rightMode, bothMode}
EVENT INITIALISATION
  action envE ≔ FALSE
  action envH ≔ FALSE
  action envP ≔ pNeutral
  action obsE ≔ FALSE
  action obsH ≔ FALSE
  action obsP ≔ pNeutral
  action active ≔ noMode
  action on ≔ FALSE
  action remaining ≔ 0
  action blinkLeft ≔ 0
  action blinkRight ≔ 0
END

EVENT Environment
  parameter e
  parameter h
  parameter p
  guard e ∈ BOOL
  guard h ∈ BOOL
  guard p ∈ POS
  action envE ≔ e
  action envH ≔ h
  action envP ≔ p
END

EVENT Cycle
  parameter e
  parameter h
  parameter p
  parameter m
  parameter b
  parameter r
  guard e ∈ BOOL
  guard h ∈ BOOL
  guard p ∈ POS
  guard m ∈ MODE
  guard b ∈ BOOL
  guard r ∈ 0‥(ticks − 1)
  guard m = command((e ↦ h) ↦ p) ∧ ((m = noMode ∧ b = FALSE ∧ r = 0) ∨ (m ≠ noMode ∧ active = noMode ∧ b = TRUE ∧ r = ticks − 1) ∨ (m ≠ noMode ∧ active ≠ noMode ∧ remaining > 0 ∧ b = on ∧ r = remaining − 1) ∨ (m ≠ noMode ∧ active ≠ noMode ∧ remaining = 0 ∧ b = bool(on = FALSE) ∧ r = ticks − 1))
  action obsE ≔ e
  action obsH ≔ h
  action obsP ≔ p
  action active ≔ m
  action on ≔ b
  action remaining ≔ r
  action blinkLeft ≔ lampL(m ↦ b)
  action blinkRight ≔ lampR(m ↦ b)
END

```

## M1_SampledCycle

```text
refinesMachine M0_AtomicCycle
seesContext C_AutomotivePilot
variable envE
variable envH
variable envP
variable obsE
variable obsH
variable obsP
variable active
variable on
variable remaining
variable blinkLeft
variable blinkRight
variable stage
variable sE
variable sH
variable sP
variable nextMode
variable nextOn
variable nextRemaining
invariant envE ∈ BOOL
invariant envH ∈ BOOL
invariant envP ∈ POS
invariant obsE ∈ BOOL
invariant obsH ∈ BOOL
invariant obsP ∈ POS
invariant active ∈ MODE
invariant on ∈ BOOL
invariant remaining ∈ 0‥(ticks − 1)
invariant blinkLeft ∈ {0, 100}
invariant blinkRight ∈ {0, 100}
invariant active = command((obsE ↦ obsH) ↦ obsP)
invariant active = noMode ⇒ (on = FALSE ∧ remaining = 0)
invariant blinkLeft = lampL(active ↦ on)
invariant blinkRight = lampR(active ↦ on)
invariant obsH = TRUE ⇒ active = bothMode
invariant obsE = FALSE ∧ obsH = FALSE ⇒ active = noMode
invariant active = bothMode ⇒ blinkLeft = blinkRight
invariant on = FALSE ⇒ (blinkLeft = 0 ∧ blinkRight = 0)
invariant blinkLeft = 100 ⇒ active ∈ {leftMode, bothMode}
invariant blinkRight = 100 ⇒ active ∈ {rightMode, bothMode}
invariant stage ∈ 0‥2
invariant sE ∈ BOOL
invariant sH ∈ BOOL
invariant sP ∈ POS
invariant nextMode ∈ MODE
invariant nextOn ∈ BOOL
invariant nextRemaining ∈ 0‥(ticks − 1)
invariant stage = 2 ⇒ (nextMode = command((sE ↦ sH) ↦ sP) ∧ ((nextMode = noMode ∧ nextOn = FALSE ∧ nextRemaining = 0) ∨ (nextMode ≠ noMode ∧ active = noMode ∧ nextOn = TRUE ∧ nextRemaining = ticks − 1) ∨ (nextMode ≠ noMode ∧ active ≠ noMode ∧ remaining > 0 ∧ nextOn = on ∧ nextRemaining = remaining − 1) ∨ (nextMode ≠ noMode ∧ active ≠ noMode ∧ remaining = 0 ∧ nextOn = bool(on = FALSE) ∧ nextRemaining = ticks − 1)))
variant 2 − stage
EVENT INITIALISATION
  action envE ≔ FALSE
  action envH ≔ FALSE
  action envP ≔ pNeutral
  action obsE ≔ FALSE
  action obsH ≔ FALSE
  action obsP ≔ pNeutral
  action active ≔ noMode
  action on ≔ FALSE
  action remaining ≔ 0
  action blinkLeft ≔ 0
  action blinkRight ≔ 0
  action stage ≔ 0
  action sE ≔ FALSE
  action sH ≔ FALSE
  action sP ≔ pNeutral
  action nextMode ≔ noMode
  action nextOn ≔ FALSE
  action nextRemaining ≔ 0
END

EVENT Environment
  refinesEvent Environment
  parameter e
  parameter h
  parameter p
  guard e ∈ BOOL
  guard h ∈ BOOL
  guard p ∈ POS
  action envE ≔ e
  action envH ≔ h
  action envP ≔ p
END

EVENT Sample
  guard stage = 0
  action sE ≔ envE
  action sH ≔ envH
  action sP ≔ envP
  action stage ≔ 1
END

EVENT Decide
  parameter m
  parameter b
  parameter r
  guard stage = 1
  guard m ∈ MODE
  guard b ∈ BOOL
  guard r ∈ 0‥(ticks − 1)
  guard m = command((sE ↦ sH) ↦ sP) ∧ ((m = noMode ∧ b = FALSE ∧ r = 0) ∨ (m ≠ noMode ∧ active = noMode ∧ b = TRUE ∧ r = ticks − 1) ∨ (m ≠ noMode ∧ active ≠ noMode ∧ remaining > 0 ∧ b = on ∧ r = remaining − 1) ∨ (m ≠ noMode ∧ active ≠ noMode ∧ remaining = 0 ∧ b = bool(on = FALSE) ∧ r = ticks − 1))
  action nextMode ≔ m
  action nextOn ≔ b
  action nextRemaining ≔ r
  action stage ≔ 2
END

EVENT Emit
  refinesEvent Cycle
  guard stage = 2
  witness e = sE
  witness h = sH
  witness p = sP
  witness m = nextMode
  witness b = nextOn
  witness r = nextRemaining
  action obsE ≔ sE
  action obsH ≔ sH
  action obsP ≔ sP
  action active ≔ nextMode
  action on ≔ nextOn
  action remaining ≔ nextRemaining
  action blinkLeft ≔ lampL(nextMode ↦ nextOn)
  action blinkRight ≔ lampR(nextMode ↦ nextOn)
  action stage ≔ 0
END

```
