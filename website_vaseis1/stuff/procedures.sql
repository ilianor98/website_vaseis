DELIMITER //

CREATE PROCEDURE `make_reservation`(IN book_ex INT, IN user_ex INT)
BEGIN
    DECLARE book_id_val INT;
    DECLARE user_id_val INT;
    DECLARE school_id_val INT;
    DECLARE book_inventory INT;
    DECLARE user_num_books INT;
    DECLARE user_has_delayed_reservation INT;
    DECLARE user_has_same_book_reservation INT;
    DECLARE user_pending_reservations INT;

    SET book_id_val = book_ex;
    SET user_id_val = user_ex;

    SET school_id_val = (SELECT school_id FROM user_school WHERE user_id = user_id_val);

    SET user_num_books = (SELECT num_books FROM user WHERE id = user_id_val);

    IF user_num_books < 2 THEN
        SET user_has_delayed_reservation = (SELECT COUNT(*) FROM reservation WHERE user_id = user_id_val AND is_delayed = 1);

        IF user_has_delayed_reservation = 0 THEN
            SET user_has_same_book_reservation = (SELECT COUNT(*) FROM reservation WHERE user_id = user_id_val AND book_id = book_id_val);

            IF user_has_same_book_reservation = 0 THEN
                SET user_pending_reservations = (SELECT COUNT(*) FROM reservation WHERE user_id = user_id_val AND reservation_status = 0);

                IF user_pending_reservations < 2 THEN
                    SET book_inventory = (SELECT inventory FROM book_school WHERE book_id = book_id_val AND school_id = school_id_val);

                    IF book_inventory > 0 THEN
                        INSERT INTO reservation (book_id, user_id, school_id, reservation_date)
                        VALUES (book_id_val, user_id_val, school_id_val, CURDATE());

                        SELECT 'Reservation made successfully.' AS message;
                    ELSE
                        SELECT 'Book is out of stock for the user''s school.' AS message;
                    END IF;
                ELSE
                    SELECT 'User has reached the maximum number of pending reservations.' AS message;
                END IF;
            ELSE
                SELECT 'User already has a reservation for the same book.' AS message;
            END IF;
        ELSE
            SELECT 'User has a delayed reservation and cannot make a new reservation.' AS message;
        END IF;
    ELSE
        SELECT 'User has reached the maximum number of books.' AS message;
    END IF;
END//

CREATE PROCEDURE approve_reservation(IN reservation_id_ex INT)
BEGIN
    UPDATE reservation
    SET is_approved = 1
    WHERE reservation_id = reservation_id_ex;
    
    SELECT 'Reservation approved successfully.' AS message;
END;

CREATE PROCEDURE borrow_book(IN reservation_id_ex INT)
BEGIN
    DECLARE book_id_val INT;
    DECLARE school_id_val INT;
    DECLARE user_id_val INT;
    
    SELECT book_id, school_id, user_id INTO book_id_val, school_id_val, user_id_val
    FROM reservation
    WHERE reservation_id = reservation_id_ex;
    
    UPDATE book_school
    SET inventory = inventory - 1
    WHERE book_id = book_id_val AND school_id = school_id_val;
    
    UPDATE user
    SET num_books = num_books + 1
    WHERE id = user_id_val;
    
    UPDATE reservation
    SET reservation_status = 1,
        borrow_date = CURDATE(),
        expected_date = CURDATE() + INTERVAL 7 DAY
    WHERE reservation_id = reservation_id_ex;
    
    SELECT 'Book borrowed successfully.' AS message;
END;

CREATE PROCEDURE check_book_inv(IN book_ex INT, IN school_ex INT)
BEGIN
    DECLARE reservation_id_val INT;
    
    SELECT reservation_id INTO reservation_id_val
    FROM reservation
    WHERE book_id = book_ex AND school_id = school_ex AND reservation_status = 0
    ORDER BY reservation_date
    LIMIT 1;
    
    IF reservation_id_val IS NOT NULL THEN
        CALL borrow_book(reservation_id_val);
    END IF;
END;

CREATE PROCEDURE return_book(IN reservation_ex INT)
BEGIN
    DECLARE book_id_val INT;
    DECLARE school_id_val INT;
    DECLARE user_id_val INT;

    SELECT book_id, school_id, user_id INTO book_id_val, school_id_val, user_id_val
    FROM reservation
    WHERE reservation_id = reservation_ex;

    UPDATE reservation
    SET return_date = CURDATE()
    WHERE reservation_id = reservation_ex;

    UPDATE book_school
    SET inventory = inventory + 1
    WHERE book_id = book_id_val AND school_id = school_id_val;

    UPDATE user
    SET num_books = num_books - 1
    WHERE id = user_id_val;

    SELECT 'Book returned successfully.' AS message;

    CALL check_book_inv(book_id_val, school_id_val);
END;
