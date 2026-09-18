-- budget_script.lua
-- Atomic Lua script for reserving budget and reconciling costs.
-- 
-- KEYS[1]: The budget usage key (e.g., 'usage:team_id:YYYY-MM')
-- ARGV[1]: Action ('RESERVE' or 'RECONCILE')
-- ARGV[2]: Amount to add/subtract (Estimated cost for RESERVE, Cost Difference for RECONCILE)
-- ARGV[3]: Maximum budget limit (Only used for RESERVE)

local usage_key = KEYS[1]
local action = ARGV[1]

if action == 'RESERVE' then
    local estimated_cost = tonumber(ARGV[2])
    local budget_limit = tonumber(ARGV[3])
    
    -- Get current usage, default to 0 if it doesn't exist
    local current_usage = tonumber(redis.call('GET', usage_key) or "0")
    
    -- Check if reservation exceeds budget
    if (current_usage + estimated_cost) > budget_limit then
        -- Return 0 to indicate rejection (over budget)
        return 0
    end
    
    -- Atomically increment the usage by the estimated cost
    redis.call('INCRBYFLOAT', usage_key, estimated_cost)
    -- Return 1 to indicate success (reservation granted)
    return 1

elseif action == 'RECONCILE' then
    -- Amount = actual_cost - estimated_cost
    -- If actual cost was lower, difference is negative. If higher, positive.
    local cost_difference = tonumber(ARGV[2])
    
    -- Atomically adjust the usage
    local new_usage = tonumber(redis.call('INCRBYFLOAT', usage_key, cost_difference))
    
    -- Sanity check: prevent usage from going below 0 in edge cases
    if new_usage < 0 then
        redis.call('SET', usage_key, 0)
    end
    
    return 1
else
    return redis.error_reply("Invalid action specified. Must be RESERVE or RECONCILE.")
end
