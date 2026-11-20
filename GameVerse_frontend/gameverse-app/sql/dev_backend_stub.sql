-- =====================================================================
--  GameVerse - DEV BACKEND STUB (frontend branch only)
-- ---------------------------------------------------------------------
--  This script exists so the frontend can be run and tested on its own
--  before it is merged with the backend branch. When the branches are
--  combined, the backend branch's SQL script REPLACES this file.
--
--  Run top-to-bottom in pgAdmin4 (or psql) on a database that already
--  has the Assignment 2/3 GameVerse schema + data loaded.
--
--  What it adds:
--    * ID defaults (sequences) so new rows can be inserted
--    * Login support: players.passwordhash + admins table (pgcrypto)
--    * linkedtxnid on gametransactions (transfer legs / reversals)
--    * Stored functions: performTransaction, transferFunds,
--      getWalletSummary, checkSufficientBalance, getLowBalanceAlerts
--    * Triggers: AFTER INSERT balance update, BEFORE INSERT inactive check
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;
SET search_path TO gameverse, public;

-- ---------------------------------------------------------------------
-- 1. ID sequences (the Assignment 2 tables have no defaults)
-- ---------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS gaminghubs_hubid_seq       OWNED BY gaminghubs.hubid;
CREATE SEQUENCE IF NOT EXISTS wallets_walletid_seq       OWNED BY wallets.walletid;
CREATE SEQUENCE IF NOT EXISTS players_playerid_seq       OWNED BY players.playerid;
CREATE SEQUENCE IF NOT EXISTS gametransactions_txnid_seq OWNED BY gametransactions.transactionid;
CREATE SEQUENCE IF NOT EXISTS walletreviews_reviewid_seq OWNED BY walletreviews.reviewid;

SELECT setval('gaminghubs_hubid_seq',       (SELECT COALESCE(MAX(hubid), 0)         FROM gaminghubs) + 1, false);
SELECT setval('wallets_walletid_seq',       (SELECT COALESCE(MAX(walletid), 2000)   FROM wallets) + 1, false);
SELECT setval('players_playerid_seq',       (SELECT COALESCE(MAX(playerid), 3000)   FROM players) + 1, false);
SELECT setval('gametransactions_txnid_seq', (SELECT COALESCE(MAX(transactionid), 8000) FROM gametransactions) + 1, false);
SELECT setval('walletreviews_reviewid_seq', (SELECT COALESCE(MAX(reviewid), 6000)   FROM walletreviews) + 1, false);

ALTER TABLE gaminghubs       ALTER COLUMN hubid         SET DEFAULT nextval('gaminghubs_hubid_seq');
ALTER TABLE wallets          ALTER COLUMN walletid      SET DEFAULT nextval('wallets_walletid_seq');
ALTER TABLE players          ALTER COLUMN playerid      SET DEFAULT nextval('players_playerid_seq');
ALTER TABLE gametransactions ALTER COLUMN transactionid SET DEFAULT nextval('gametransactions_txnid_seq');
ALTER TABLE walletreviews    ALTER COLUMN reviewid      SET DEFAULT nextval('walletreviews_reviewid_seq');

ALTER TABLE gametransactions ALTER COLUMN transactiondate SET DEFAULT CURRENT_DATE;
ALTER TABLE walletreviews    ALTER COLUMN reviewdate      SET DEFAULT CURRENT_DATE;
ALTER TABLE walletreviews    ALTER COLUMN isverified      SET DEFAULT FALSE;
ALTER TABLE players          ALTER COLUMN registrationdate SET DEFAULT CURRENT_DATE;
ALTER TABLE players          ALTER COLUMN isactive        SET DEFAULT TRUE;
ALTER TABLE gaminghubs       ALTER COLUMN isactive        SET DEFAULT TRUE;
ALTER TABLE wallets          ALTER COLUMN isactive        SET DEFAULT TRUE;
ALTER TABLE wallets          ALTER COLUMN opendate        SET DEFAULT CURRENT_DATE;

-- ---------------------------------------------------------------------
-- 2. Login support
-- ---------------------------------------------------------------------
ALTER TABLE players ADD COLUMN IF NOT EXISTS passwordhash text;

CREATE TABLE IF NOT EXISTS admins (
    adminid      serial PRIMARY KEY,
    username     varchar(50) NOT NULL UNIQUE,
    passwordhash text        NOT NULL
);

-- Test credentials (documented in README_FRONTEND.md)
--   admin  / Admin@123
--   every seeded player / player123
INSERT INTO admins (username, passwordhash)
VALUES ('admin', crypt('Admin@123', gen_salt('bf')))
ON CONFLICT (username) DO NOTHING;

UPDATE players SET passwordhash = crypt('player123', gen_salt('bf'))
WHERE passwordhash IS NULL;

-- ---------------------------------------------------------------------
-- 3. Transfer / reversal linking
-- ---------------------------------------------------------------------
ALTER TABLE gametransactions ADD COLUMN IF NOT EXISTS linkedtxnid integer
    REFERENCES gametransactions(transactionid);

-- Link the existing Assignment 2 transfer pairs (8006/8007, 8017/8018, 8026/8027)
UPDATE gametransactions o SET linkedtxnid = i.transactionid
FROM gametransactions i
WHERE o.transactiontype = 'Transfer' AND i.transactiontype = 'Transfer'
  AND o.amount < 0 AND i.amount = -o.amount
  AND i.transactiondate = o.transactiondate
  AND i.recipient = 'From Wallet ' || o.walletid
  AND o.recipient = 'Wallet ' || i.walletid
  AND o.linkedtxnid IS NULL;
UPDATE gametransactions i SET linkedtxnid = o.transactionid
FROM gametransactions o
WHERE o.linkedtxnid = i.transactionid AND i.linkedtxnid IS NULL;

-- ---------------------------------------------------------------------
-- 4. Helper: money formatting used in error messages ("2,400.00")
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fmt_money(p numeric) RETURNS text
LANGUAGE sql IMMUTABLE AS $$
    SELECT to_char(p, 'FM999,999,999,990.00');
$$;

-- ---------------------------------------------------------------------
-- 5. checkSufficientBalance(walletID, requestedAmount) -> boolean
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION checkSufficientBalance(p_walletid integer, p_amount numeric)
RETURNS boolean LANGUAGE plpgsql AS $$
DECLARE
    v_balance numeric; v_min numeric;
BEGIN
    SELECT balance, minimumbalance INTO v_balance, v_min
    FROM wallets WHERE walletid = p_walletid;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Wallet % does not exist.', p_walletid;
    END IF;
    RETURN (v_balance - p_amount) >= v_min;
END;
$$;

-- Internal helper that raises the standard "Insufficient funds" message
CREATE OR REPLACE FUNCTION assert_sufficient_balance(p_walletid integer, p_amount numeric)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE
    v_balance numeric; v_min numeric;
BEGIN
    IF NOT checkSufficientBalance(p_walletid, p_amount) THEN
        SELECT balance, minimumbalance INTO v_balance, v_min FROM wallets WHERE walletid = p_walletid;
        RAISE EXCEPTION 'Insufficient funds. Spendable balance: % (balance %, minimum %)',
            fmt_money(GREATEST(v_balance - v_min, 0)), fmt_money(v_balance), fmt_money(v_min);
    END IF;
END;
$$;

-- ---------------------------------------------------------------------
-- 6. performTransaction(walletID, amount, type, paymentMethod, recipient)
--    amount is passed POSITIVE; sign is applied here. Not for Transfer.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION performTransaction(
    p_walletid integer, p_amount numeric, p_type varchar,
    p_method varchar, p_recipient varchar)
RETURNS integer LANGUAGE plpgsql AS $$
DECLARE
    v_id integer; v_signed numeric;
BEGIN
    IF p_amount IS NULL OR p_amount <= 0 THEN
        RAISE EXCEPTION 'Amount must be greater than zero.';
    END IF;
    IF p_type = 'Transfer' THEN
        RAISE EXCEPTION 'Use transferFunds for transfers.';
    ELSIF p_type NOT IN ('TopUp', 'Cashout', 'Purchase') THEN
        RAISE EXCEPTION 'Unknown transaction type: %', p_type;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM wallets WHERE walletid = p_walletid) THEN
        RAISE EXCEPTION 'Wallet % does not exist.', p_walletid;
    END IF;

    IF p_type = 'TopUp' THEN
        v_signed := p_amount;
    ELSE
        PERFORM assert_sufficient_balance(p_walletid, p_amount);
        v_signed := -p_amount;
    END IF;

    INSERT INTO gametransactions (walletid, transactiondate, amount, transactiontype, recipient, paymentmethod)
    VALUES (p_walletid, CURRENT_DATE, v_signed, p_type, COALESCE(NULLIF(p_recipient, ''), 'Self'), p_method)
    RETURNING transactionid INTO v_id;
    RETURN v_id;
END;
$$;

-- ---------------------------------------------------------------------
-- 7. transferFunds(fromWalletID, toWalletID, amount, paymentMethod)
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION transferFunds(
    p_from integer, p_to integer, p_amount numeric, p_method varchar)
RETURNS integer LANGUAGE plpgsql AS $$
DECLARE
    v_out integer; v_in integer;
BEGIN
    IF p_amount IS NULL OR p_amount <= 0 THEN
        RAISE EXCEPTION 'Amount must be greater than zero.';
    END IF;
    IF p_from = p_to THEN
        RAISE EXCEPTION 'Source and destination wallets must be different.';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM wallets WHERE walletid = p_to) THEN
        RAISE EXCEPTION 'Destination wallet % does not exist.', p_to;
    END IF;
    PERFORM assert_sufficient_balance(p_from, p_amount);

    INSERT INTO gametransactions (walletid, transactiondate, amount, transactiontype, recipient, paymentmethod)
    VALUES (p_from, CURRENT_DATE, -p_amount, 'Transfer', 'Wallet ' || p_to, p_method)
    RETURNING transactionid INTO v_out;

    INSERT INTO gametransactions (walletid, transactiondate, amount, transactiontype, recipient, paymentmethod, linkedtxnid)
    VALUES (p_to, CURRENT_DATE, p_amount, 'Transfer', 'From Wallet ' || p_from, p_method, v_out)
    RETURNING transactionid INTO v_in;

    UPDATE gametransactions SET linkedtxnid = v_in WHERE transactionid = v_out;
    RETURN v_out;
END;
$$;

-- ---------------------------------------------------------------------
-- 8. getWalletSummary(walletID)
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION getWalletSummary(p_walletid integer)
RETURNS TABLE (balance numeric, total_topups numeric, total_cashouts numeric,
               total_purchases numeric, transfers_in numeric, transfers_out numeric,
               transaction_count bigint)
LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM wallets w WHERE w.walletid = p_walletid) THEN
        RAISE EXCEPTION 'Wallet % does not exist.', p_walletid;
    END IF;
    RETURN QUERY
    SELECT w.balance,
           COALESCE(SUM(t.amount) FILTER (WHERE t.transactiontype = 'TopUp'), 0),
           COALESCE(-SUM(t.amount) FILTER (WHERE t.transactiontype = 'Cashout'), 0),
           COALESCE(-SUM(t.amount) FILTER (WHERE t.transactiontype = 'Purchase'), 0),
           COALESCE(SUM(t.amount) FILTER (WHERE t.transactiontype = 'Transfer' AND t.amount > 0), 0),
           COALESCE(-SUM(t.amount) FILTER (WHERE t.transactiontype = 'Transfer' AND t.amount < 0), 0),
           COUNT(t.transactionid)
    FROM wallets w
    LEFT JOIN gametransactions t ON t.walletid = w.walletid
    WHERE w.walletid = p_walletid
    GROUP BY w.balance;
END;
$$;

-- ---------------------------------------------------------------------
-- 9. getLowBalanceAlerts(threshold)
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION getLowBalanceAlerts(p_threshold numeric)
RETURNS TABLE (walletid integer, wallettype varchar, balance numeric,
               minimumbalance numeric, hubname varchar)
LANGUAGE sql AS $$
    SELECT w.walletid, w.wallettype, w.balance, w.minimumbalance, h.hubname
    FROM wallets w JOIN gaminghubs h ON h.hubid = w.hubid
    WHERE w.isactive AND w.balance < p_threshold
    ORDER BY w.balance;
$$;

-- ---------------------------------------------------------------------
-- 10. Triggers
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_reject_inactive_wallet() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM wallets WHERE walletid = NEW.walletid AND isactive) THEN
        RAISE EXCEPTION 'Wallet % is inactive. Transactions are not allowed.', NEW.walletid;
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION trg_apply_balance() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE wallets SET balance = balance + NEW.amount WHERE walletid = NEW.walletid;
    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS trg_txn_reject_inactive ON gametransactions;
CREATE TRIGGER trg_txn_reject_inactive
    BEFORE INSERT ON gametransactions
    FOR EACH ROW EXECUTE FUNCTION trg_reject_inactive_wallet();

DROP TRIGGER IF EXISTS trg_txn_apply_balance ON gametransactions;
CREATE TRIGGER trg_txn_apply_balance
    AFTER INSERT ON gametransactions
    FOR EACH ROW EXECUTE FUNCTION trg_apply_balance();
