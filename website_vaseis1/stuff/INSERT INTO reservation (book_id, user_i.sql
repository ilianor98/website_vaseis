INSERT INTO reservation (book_id, user_id, reservation_date, borrow_date, expected_date, return_date, reservation_status, is_approved, school_id)
SELECT 
    (SELECT ISBN FROM book ORDER BY RAND() LIMIT 1) AS book_id,
    FLOOR(RAND() * 403) + 1 AS user_id,
    "2023-05-01" as reservation_date,
    "2023-05-02" as borrow_date,
    "2023-05-09" as expected_date,
    "2023-05-08" as return_date,
    1 AS reservation_status,
    1 AS is_approved,
    1 AS school_id
FROM
    user, book, school
LIMIT 8;

INSERT INTO reservation (book_id, user_id, reservation_date,is_approved,school_id)
SELECT 
    (SELECT ISBN FROM book ORDER BY RAND() LIMIT 1) AS book_id,
    FLOOR(RAND() * 403) + 1 AS user_id,
    "2023-06-08",
    1,
    FLOOR(RAND() * 3) + 1 AS school_id
FROM
    user, book, school
LIMIT 30;

UPDATE reservation set is_delayed = 1 where return_date > expected_date;


SELECT s1.admin_name,
FROM school s1
INNER JOIN (
  SELECT school_id, COUNT(*) AS reservation_count
  FROM reservation
  GROUP BY school_id
  HAVING COUNT(*) > 20
) s2 ON s1.id = s2.school_id
INNER JOIN (
  SELECT COUNT(*) AS reservation_count
  FROM reservation
  GROUP BY school_id
  HAVING COUNT(*) > 20
) s3 ON s2.reservation_count = s3.reservation_count
GROUP BY s1.admin_name
HAVING COUNT(*) > 1;

UPDATE user
SET num_books = (
    SELECT COUNT(*) 
    FROM reservation 
    WHERE reservation.user_id = user.id
    AND reservation.return_date IS NULL
    AND reservation.borrow_date IS NOT NULL
);

