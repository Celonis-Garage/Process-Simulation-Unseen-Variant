# 📋 REVISED Test Scenarios - Using Only Dataset Activities

## Available Activities in O2C Dataset
Based on `common_activities` in `backend/utils.py`:

1. Receive Customer Order
2. Validate Customer Order
3. Perform Credit Check
4. Approve Order
5. **Reject Order** (in dataset but not in most frequent variant)
6. Schedule Order Fulfillment
7. Generate Pick List
8. Pack Items
9. Generate Shipping Label
10. Ship Order
11. Generate Invoice
12. **Apply Discount** (in dataset but not in most frequent variant)
13. **Process Return Request** (in dataset but not in most frequent variant)

**Most Frequent Variant** (baseline): Activities 1-4, 6-11 (10 activities)

---

## Test Categories

### CATEGORY 1: Baseline & Consistency
### CATEGORY 2: Single Step Addition (Dataset Activities Only)
### CATEGORY 3: Single Step Removal
### CATEGORY 4: Multiple Step Changes
### CATEGORY 5: KPI Modifications (Time Changes)
### CATEGORY 6: KPI Modifications (Cost Changes)
### CATEGORY 7: Complex Scenarios

---

## CATEGORY 1: BASELINE & CONSISTENCY TESTS

### Test 1.1: Baseline Process (No Changes)
**Prompt**: None (default)  
**Activities**: Standard 10 activities  
**Expected**: 0% change on all KPIs  
**Entities**: Should be consistent (deterministic seeding)

### Test 1.2: Baseline Process (Second Run)
**Prompt**: None (default)  
**Expected**: Identical to Test 1.1 (same entities, same KPIs)  
**Purpose**: Verify deterministic seeding

---

## CATEGORY 2: SINGLE STEP ADDITION (Dataset Activities Only)

### Test 2.1: Add "Process Return Request"
**Prompt**: `Add "Process Return Request" after "Generate Pick List"`  
**Activities**: Baseline + Process Return Request (11 activities)  
**Activity Delta**: +1  
**Expected KPI Changes**: ~2% penalty (complexity adjustment)  
**Real-World Impact**: Returns add processing time, may delay fulfillment  
**Why This Activity**: Exists in dataset but not in baseline

### Test 2.2: Add "Apply Discount"
**Prompt**: `Add "Apply Discount" after "Approve Order"`  
**Activities**: Baseline + Apply Discount (11 activities)  
**Activity Delta**: +1  
**Expected**: ~2% penalty  
**Real-World Impact**: Discount application adds admin overhead  
**Why This Activity**: Exists in dataset but not in baseline

### Test 2.3: Add "Reject Order"
**Prompt**: `Add "Reject Order" after "Perform Credit Check"`  
**Activities**: Baseline + Reject Order (11 activities)  
**Activity Delta**: +1  
**Expected**: ~2% penalty, but likely higher due to rejection overhead  
**Real-World Impact**: Rejection handling adds complexity, reduces revenue  
**Why This Activity**: Critical path activity in dataset

---

## CATEGORY 3: SINGLE STEP REMOVAL

### Test 3.1: Remove "Generate Shipping Label"
**Prompt**: `Remove "Generate Shipping Label"`  
**Activities**: Baseline - Generate Shipping Label (9 activities)  
**Activity Delta**: -1  
**Expected (Rule)**: +2% bonus  
**Expected (ML)**: Penalty (missing critical step)  
**Real-World Impact**: Missing labels cause delivery errors  
**Purpose**: Test if ML overrides simplistic rule

### Test 3.2: Remove "Schedule Order Fulfillment"
**Prompt**: `Remove "Schedule Order Fulfillment"`  
**Activities**: Baseline - Schedule Order Fulfillment (9 activities)  
**Activity Delta**: -1  
**Expected (Rule)**: +2% bonus  
**Expected (ML)**: May vary (scheduling helps or hinders efficiency)  
**Real-World Impact**: Without scheduling, might be more agile or more chaotic

### Test 3.3: Remove "Approve Order"
**Prompt**: `Remove "Approve Order"`  
**Activities**: Baseline - Approve Order (9 activities)  
**Activity Delta**: -1  
**Expected (Rule)**: +2% bonus  
**Expected (ML)**: Penalty (missing control gate)  
**Real-World Impact**: No approval = higher risk of errors, bad debt  
**Purpose**: Test ML detection of critical control steps

---

## CATEGORY 4: MULTIPLE STEP CHANGES

### Test 4.1: Add Two Dataset Activities
**Prompt**: `Add "Apply Discount" after "Approve Order" and add "Process Return Request" after "Ship Order"`  
**Activities**: Baseline + Apply Discount + Process Return Request (12 activities)  
**Activity Delta**: +2  
**Expected**: ~4% penalty  
**Real-World Impact**: Both add overhead (discount processing + return handling)

### Test 4.2: Remove Two Steps
**Prompt**: `Remove "Generate Shipping Label" and remove "Schedule Order Fulfillment"`  
**Activities**: Baseline - Generate Shipping Label - Schedule (8 activities)  
**Activity Delta**: -2  
**Expected (Rule)**: +4% bonus  
**Expected (ML)**: May show penalty for missing label, bonus for removing schedule  
**Purpose**: Test net effect of removing different types of steps

### Test 4.3: Mixed (Add + Remove)
**Prompt**: `Add "Process Return Request" after "Ship Order" and remove "Schedule Order Fulfillment"`  
**Activities**: Baseline + Process Return - Schedule (10 activities)  
**Activity Delta**: 0  
**Expected (Rule)**: 0% (net zero complexity)  
**Expected (ML)**: Likely change due to composition shift  
**Purpose**: Test that composition matters more than count

---

## CATEGORY 5: KPI MODIFICATIONS - TIME CHANGES

### Test 5.1: Increase Time Moderately
**Prompt**: `Change "Generate Invoice" time to 30 minutes`  
**Baseline Time**: ~2-3 minutes (estimated)  
**New Time**: 30 minutes  
**Change**: ~10x increase  
**Expected**: DSO increases (invoicing delay), cost may increase  
**Real-World Impact**: Slow invoicing delays payment collection

### Test 5.2: Decrease Time Significantly
**Prompt**: `Change "Perform Credit Check" time to 1 minute`  
**Baseline Time**: ~10-15 minutes (estimated)  
**New Time**: 1 minute  
**Change**: ~10x decrease  
**Expected**: Cycle time improves, DSO improves, cost may decrease  
**Real-World Impact**: Automated credit checks speed process  
**Purpose**: Test if reduced activity time improves KPIs

### Test 5.3: Increase Time for Multiple Activities
**Prompt**: `Change "Validate Customer Order" time to 1 hour and change "Perform Credit Check" time to 2 hours`  
**Changes**: Two activities with significant time increases  
**Expected**: Major cycle time increase, DSO increase, possible cost increase  
**Real-World Impact**: Manual validation/checks slow entire process

### Test 5.4: Set Very Short Time
**Prompt**: `Change "Pack Items" time to 30 seconds`  
**Baseline Time**: ~1-2 hours (estimated)  
**New Time**: 0.5 minutes  
**Change**: Massive decrease  
**Expected**: Cycle time improves significantly  
**Real-World Impact**: Automated packing dramatically speeds fulfillment  
**Purpose**: Test extreme time reduction

---

## CATEGORY 6: KPI MODIFICATIONS - COST CHANGES

### Test 6.1: Increase Cost Moderately
**Prompt**: `Change "Ship Order" cost to $200`  
**Baseline Cost**: ~$30-50 (estimated)  
**New Cost**: $200  
**Change**: ~4-6x increase  
**Expected**: Avg Cost Delivery increases significantly  
**Real-World Impact**: Expedited/premium shipping

### Test 6.2: Decrease Cost
**Prompt**: `Change "Perform Credit Check" cost to $5`  
**Baseline Cost**: ~$20-30 (estimated)  
**New Cost**: $5  
**Change**: ~4-6x decrease  
**Expected**: Avg Cost Delivery decreases  
**Real-World Impact**: Automated credit check service  
**Purpose**: Test cost reduction impact

### Test 6.3: Set Very High Cost
**Prompt**: `Change "Pack Items" cost to $500`  
**Baseline Cost**: ~$20-40 (estimated)  
**New Cost**: $500  
**Change**: ~10-25x increase  
**Expected**: Major cost increase  
**Real-World Impact**: Custom/specialized packing  
**Purpose**: Test extreme cost scenario

### Test 6.4: Mixed Time & Cost Changes
**Prompt**: `Change "Generate Invoice" time to 5 minutes and cost to $10`  
**Changes**: Both time and cost for same activity  
**Expected**: Both time and cost KPIs affected  
**Purpose**: Test combined KPI modification

---

## CATEGORY 7: COMPLEX SCENARIOS

### Test 7.1: Add Return Processing Path
**Prompt**: `Add "Reject Order" after "Perform Credit Check" and add "Process Return Request" after "Ship Order"`  
**Activities**: Baseline + Reject Order + Process Return Request (12 activities)  
**Activity Delta**: +2  
**Expected**: ~4% penalty, possibly higher due to rejection/return overhead  
**Real-World Impact**: Complete order rejection and return handling

### Test 7.2: Streamline Payment Path
**Prompt**: `Remove "Approve Order" and change "Perform Credit Check" time to 1 minute`  
**Changes**: Remove control step + speed up validation  
**Expected**: Mixed - time improves but risk increases  
**Purpose**: Test trade-off between speed and control

### Test 7.3: Premium Service Configuration
**Prompt**: `Change "Ship Order" cost to $300 and change "Ship Order" time to 4 hours`  
**Changes**: Higher cost but much faster shipping  
**Expected**: Cost increases significantly, on-time delivery improves  
**Real-World Impact**: Express/overnight shipping  
**Purpose**: Test premium service model

### Test 7.4: Budget Optimization
**Prompt**: `Change "Perform Credit Check" cost to $5, change "Ship Order" cost to $15, and change "Generate Invoice" cost to $3`  
**Changes**: Reduce costs on 3 key activities  
**Expected**: Significant cost reduction  
**Real-World Impact**: Automation/outsourcing to reduce costs  
**Purpose**: Test multiple cost reductions

### Test 7.5: Add Discount with Return Handling
**Prompt**: `Add "Apply Discount" after "Approve Order", add "Process Return Request" after "Ship Order", and change "Process Return Request" cost to $100`  
**Changes**: Add 2 activities + modify cost of one  
**Expected**: Complex - discount may help, returns hurt, high return cost  
**Purpose**: Test combination of structure and KPI changes

---

## Test Execution Strategy

### For Each Test:
1. **Start from baseline** (reload frontend if needed)
2. **Execute prompt** (or API call for baseline)
3. **Capture results**:
   - All 5 KPIs (baseline vs predicted)
   - Entity details (users, items, suppliers)
   - Summary explanation
4. **Compare with expectations**:
   - Direction (better/worse)
   - Magnitude (close to expected?)
   - ML vs Rule behavior
5. **Analyze discrepancies**:
   - Why did ML predict differently?
   - Is the result realistic?
   - Does it make business sense?

### Success Criteria:
- ✅ Baseline: 0% change
- ✅ Consistency: Identical results on repeat
- ✅ Direction: Correct better/worse prediction
- ⚠️ Magnitude: Within 3x of expected (not exact match required)
- ✅ KPI Modifications: Changes reflected in predictions
- ✅ ML Logic: Overrides simplistic rules when appropriate

---

## Expected System Behavior

### What Should Work:
1. ✅ Baseline detection (0% change)
2. ✅ Deterministic entities (same process = same results)
3. ✅ Activity validation (only dataset activities allowed)
4. ✅ KPI modifications applied to event log
5. ✅ KPI modifications influence simulation
6. ✅ ML predictions override simplistic +/-2% rule

### What May Vary:
1. ⚠️ Exact percentages (ML predictions vary based on composition)
2. ⚠️ Magnitude (can be 1-20% instead of expected 2%)
3. ⚠️ Direction for removals (ML may disagree with "fewer steps = better")

### Known Limitations:
1. ❌ System doesn't distinguish activity semantic types (value-add vs overhead)
2. ❌ Entities change when activities change (deterministic but coupled)
3. ❌ No confidence intervals on predictions
4. ❌ Explanations are generic, not specific to changes

---

## Summary

**Total Tests**: 22 tests across 7 categories
- Baseline: 2
- Addition: 3  
- Removal: 3
- Multiple: 3
- Time Modifications: 4
- Cost Modifications: 4
- Complex: 5

**All activities used**: From O2C dataset common_activities list
**All prompts**: Valid for current system implementation
**Focus**: Realistic business scenarios with measurable impacts


